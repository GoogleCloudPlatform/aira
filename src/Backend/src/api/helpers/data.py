"""
Data related stuff.
"""

import csv
import datetime
import os
import typing
import urllib.parse
import uuid
from collections import defaultdict

import sqlalchemy.orm.collections

from api import db, errors, ports


async def handle_import(
    file_url: str, mapping: dict[str, str], storage: ports.Storage
) -> tuple[
    list[uuid.UUID],
    list[str],
    defaultdict[str | uuid.UUID, list[dict[str, typing.Any]]],
]:
    """
    Function to handle data from imports
    """
    file_data = urllib.parse.unquote(file_url)
    file_stripped = (
        file_data.replace("https://", "")
        .replace("http://", "")
        .replace("storage.googleapis.com/", "")
    )
    file_path = file_stripped.split("/", 1)[1]
    file_name = file_path.rsplit("/", 1)[1] if "/" in file_path else file_path
    download_path = await storage.download(f"gs://{file_stripped}", file_name)
    model_ids = []
    customer_ids = []
    result = defaultdict(list)
    cid_key = next((k for k, v in mapping.items() if v == "customer_id"), "customer_id")
    pid_key = next((k for k, v in mapping.items() if v == "id"), "id")
    with open(download_path, encoding="utf-8") as f:
        match download_path.rsplit(".")[1].casefold():
            case "csv":
                reader = csv.DictReader(f)
                for row in reader:
                    c_id: str | None = row.get(cid_key)
                    p_id = uuid.UUID(row.get(pid_key)) if row.get(pid_key) else None
                    if c_id:
                        customer_ids.append(c_id)
                    if p_id:
                        model_ids.append(p_id)

                    # Getting ids, higher priority from ids then customer_id
                    # If neither exist, it should create a new user
                    key = p_id or c_id or ""
                    temp_result = {}
                    for k, v in row.items():
                        # Getting correct key name from mapping,
                        # if its not there use the stored key
                        temp_key = mapping.get(k, k)
                        temp_result[temp_key] = v
                    result[key].append(temp_result)
            case _:
                raise errors.NotSupported()
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
