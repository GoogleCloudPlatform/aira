"""
Data related stuff.
"""

import csv
import datetime
import hmac
import logging
import os
import re
import typing
import urllib.parse
import uuid
from collections import defaultdict

import sqlalchemy.orm.collections

from api import db, errors, ports
from api.helpers import schemas as helper_schemas

logger = logging.getLogger(__name__)

_ALLOWED_GCS_HOSTS: frozenset[str] = frozenset(
    {"storage.googleapis.com", "storage.cloud.google.com"}
)
_SAFE_BUCKET_RE = re.compile(r"[a-z0-9][a-z0-9._-]{1,220}[a-z0-9]", re.ASCII)
_ENCODED_TRAVERSAL_RE = re.compile(r"%(?:2[ef]|5c|00)", re.IGNORECASE)


def _has_control_chars(value: str) -> bool:
    return any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)


def _safe_remove_file(path: str | None) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            logger.warning("Failed to clean up temporary import file.")


def _extract_import_bucket_and_object_path(file_url: str) -> tuple[str, str]:
    """Parse an https:// or gs:// import URL and extract (bucket, raw_object_path)."""
    if (
        not isinstance(file_url, str)
        or not file_url
        or file_url != file_url.strip()
        or _has_control_chars(file_url)
        or "\\" in file_url
        or "?" in file_url
        or "#" in file_url
        or _ENCODED_TRAVERSAL_RE.search(file_url)
    ):
        raise errors.InvalidField("url")

    parsed = urllib.parse.urlparse(file_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise errors.InvalidField("url") from exc

    if (
        parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or "@" in parsed.netloc
        or ":" in parsed.netloc
        or not parsed.path.startswith("/")
        or parsed.path.startswith("//")
    ):
        raise errors.InvalidField("url")

    if parsed.scheme == "https":
        if parsed.netloc.lower() not in _ALLOWED_GCS_HOSTS:
            raise errors.InvalidField("url")
        raw_path = parsed.path[1:]
        if "/" not in raw_path:
            raise errors.InvalidField("url")
        bucket, raw_object_path = raw_path.split("/", 1)
    elif parsed.scheme == "gs":
        bucket = parsed.netloc
        raw_object_path = parsed.path[1:]
    else:
        raise errors.InvalidField("url")

    if not bucket or "%" in bucket:
        raise errors.InvalidField("url")
    return bucket, raw_object_path


def validate_import_gcs_url(
    file_url: str,
    raw_expected_bucket: typing.Any,
    *,
    expected_import_type: helper_schemas.ImportType | None = None,
) -> tuple[str, str]:
    """Validate an import URL against the configured GCS bucket and import prefix."""
    expected_bucket = (
        raw_expected_bucket.strip() if isinstance(raw_expected_bucket, str) else ""
    )
    if not expected_bucket or not _SAFE_BUCKET_RE.fullmatch(expected_bucket):
        logger.error("GCS bucket_path setting is missing or invalid; failing closed.")
        raise errors.Forbidden()

    bucket, raw_object_path = _extract_import_bucket_and_object_path(file_url)
    if not hmac.compare_digest(bucket.encode("utf-8"), expected_bucket.encode("utf-8")):
        raise errors.InvalidField("url")

    object_path = urllib.parse.unquote(raw_object_path)
    if (
        not object_path
        or object_path.startswith("/")
        or object_path.endswith("/")
        or "\\" in object_path
        or _has_control_chars(object_path)
        or _ENCODED_TRAVERSAL_RE.search(object_path)
    ):
        raise errors.InvalidField("url")

    segments = object_path.split("/")
    if any(
        not seg
        or seg in {".", ".."}
        or seg.startswith("-")
        or "\\" in seg
        or _has_control_chars(seg)
        for seg in segments
    ):
        raise errors.InvalidField("url")

    if len(segments) < 2 or segments[0] != "import":
        raise errors.InvalidField("url")

    if expected_import_type is not None and (
        len(segments) != 3 or segments[1] != expected_import_type.value
    ):
        raise errors.InvalidField("url")

    basename = segments[-1]
    if "." not in basename or basename.rsplit(".", 1)[1].casefold() != "csv":
        raise errors.NotSupported()

    return expected_bucket, object_path


async def handle_import(
    file_url: str,
    mapping: dict[str, str],
    storage: ports.Storage,
    expected_bucket: typing.Any,
    *,
    expected_import_type: helper_schemas.ImportType | None = None,
) -> tuple[
    list[uuid.UUID],
    list[str],
    defaultdict[str | uuid.UUID, list[dict[str, typing.Any]]],
]:
    """
    Function to handle data from imports
    """
    bucket, object_path = validate_import_gcs_url(
        file_url,
        expected_bucket,
        expected_import_type=expected_import_type,
    )
    local_file_name = f"import-{uuid.uuid4().hex}.csv"
    download_path: str | None = None
    model_ids: list[uuid.UUID] = []
    customer_ids: list[str] = []
    result: defaultdict[str | uuid.UUID, list[dict[str, typing.Any]]] = defaultdict(
        list
    )
    cid_key = next((k for k, v in mapping.items() if v == "customer_id"), "customer_id")
    pid_key = next((k for k, v in mapping.items() if v == "id"), "id")
    try:
        download_path = await storage.download(
            f"gs://{bucket}/{object_path}", local_file_name
        )
        if os.path.splitext(download_path)[1].casefold() != ".csv":
            raise errors.NotSupported()
        with open(download_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                c_id: str | None = row.get(cid_key)
                raw_pid = row.get(pid_key)
                p_id = uuid.UUID(raw_pid) if raw_pid else None
                if c_id:
                    customer_ids.append(c_id)
                if p_id:
                    model_ids.append(p_id)

                # Getting ids, higher priority from ids then customer_id
                # If neither exist, it should create a new user
                key: str | uuid.UUID = p_id or c_id or ""
                temp_result: dict[str, typing.Any] = {}
                for k, v in row.items():
                    # Getting correct key name from mapping,
                    # if its not there use the stored key
                    temp_key = mapping.get(k, k)
                    temp_result[temp_key] = v
                result[key].append(temp_result)
    finally:
        _safe_remove_file(download_path)
    return model_ids, customer_ids, result


async def handle_export(
    objs: list[typing.Any],
    export_keys: list[str],
    user_id: uuid.UUID,
    exp_type: str,
    storage: ports.Storage,
    fmt: str = "csv",
    delimiter: str = ",",
) -> str:
    """
    Function to handle data from exports
    """
    path = f"/tmp/{user_id}/{exp_type}"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    local_file = f"{path}/export.csv"
    result: list[list[typing.Any]] = [export_keys]
    for obj in objs:
        temp_result: list[typing.Any] = []
        for key in export_keys:
            match getattr(obj, key):
                case sqlalchemy.orm.collections.InstrumentedList():
                    temp_result.append([str(obj.id) for obj in getattr(obj, key)])
                case db.Base():
                    temp_result.append(str(getattr(obj, key).id))
                case uuid.UUID():
                    temp_result.append(str(getattr(obj, key)))
                case _:
                    temp_result.append(getattr(obj, key))
        result.append(temp_result)

    match fmt:
        case "csv":
            mimetype = "text/csv"
            with open(
                local_file,
                "w",
                newline="",
                encoding="utf-8",
            ) as f:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerows(result)
        case _:
            raise NotImplementedError()
    now = datetime.datetime.now().strftime("%Y%m%d")
    file_path = f"export/{now}-{user_id.hex}-{exp_type}.{fmt}"
    await storage.upload_by_file(file_path, local_file)
    signed_url = await storage.generate_signed_url(file_path, mimetype, method="GET")
    return signed_url
