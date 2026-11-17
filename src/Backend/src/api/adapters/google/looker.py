"""
Module related to looker.
"""

import base64
import collections.abc
import hmac
import json
import logging
import re
import time
import typing
import urllib.parse
import uuid
from hashlib import sha1

from starlette import datastructures

from api import errors, ports
from api.helpers import UUIDEncoder
from api.models import User as UserModel

logger = logging.getLogger(__name__)

_MINIMAL_EMBED_PERMISSIONS: tuple[str, ...] = (
    "access_data",
    "see_lookml_dashboards",
    "see_user_dashboards",
)
_DASHBOARD_PATH_RE = re.compile(
    r"/embed/dashboards/([A-Za-z0-9_-]+(?:::[A-Za-z0-9_-]+)?)",
    re.ASCII,
)
_SDK_VERSION_RE = re.compile(r"[0-9]+", re.ASCII)
_HOST_RE = re.compile(r"[A-Za-z0-9.-]+(?::[0-9]{1,5})?", re.ASCII)
_ALLOWED_EMBED_QUERY_KEYS = frozenset({"embed_domain", "sdk"})


def _has_control_chars(value: str) -> bool:
    return any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)


def _normalize_origin(
    raw_origin: str, *, allow_root_slash: bool = False
) -> str | None:
    """Normalize an http(s) origin to 'scheme://host[:port]', or return None."""
    if (
        not raw_origin
        or raw_origin == "*"
        or _has_control_chars(raw_origin)
        or any(ch.isspace() for ch in raw_origin)
        or "\\" in raw_origin
    ):
        return None

    try:
        parsed = urllib.parse.urlsplit(raw_origin)
        port = parsed.port
    except ValueError:
        return None

    scheme = parsed.scheme.lower()
    allowed_paths = ("", "/") if allow_root_slash else ("",)
    invalid = (
        scheme not in {"http", "https"}
        or not parsed.hostname
        or "*" in parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.query)
        or bool(parsed.fragment)
        or parsed.path not in allowed_paths
    )
    if invalid:
        return None

    assert parsed.hostname is not None
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    netloc = f"{host}:{port}" if port is not None else host
    return f"{scheme}://{netloc}"


# pylint: disable=too-many-instance-attributes
class User:
    """
    Class with user data for looker.
    """

    def __init__(
        self,
        external_user_id: uuid.UUID,
        first_name: str | None = None,
        last_name: str | None = None,
        permissions: list[str] | None = None,
        models_data: list[str] | None = None,
        group_ids: list[int] | None = None,
        external_group_id: uuid.UUID | None = None,
        user_attributes: dict[str, typing.Any] | None = None,
        access_filters: dict[str, typing.Any] | None = None,
        force_logout_login: bool = True,
        session_length: int = 3000,
    ):
        self.external_user_id = json.dumps(external_user_id, cls=UUIDEncoder)
        self.first_name = json.dumps(first_name)
        self.last_name = json.dumps(last_name)
        self.permissions = json.dumps(permissions if permissions else [])
        self.models = json.dumps(models_data if models_data else [])
        self.access_filters = json.dumps(
            access_filters if access_filters else {}, cls=UUIDEncoder
        )
        self.user_attributes = json.dumps(
            user_attributes if user_attributes else {}, cls=UUIDEncoder
        )
        self.group_ids = json.dumps(group_ids if group_ids else [], cls=UUIDEncoder)
        self.external_group_id = json.dumps(external_group_id, cls=UUIDEncoder)
        self.force_logout_login = json.dumps(force_logout_login)
        self.session_length = json.dumps(session_length)


class LookerDashboard(ports.Dashboard):
    """
    The adapter for dashboard.
    """

    def __init__(
        self,
        looker_host: str,
        looker_secret: str,
        allowed_dashboard_ids: collections.abc.Collection[str] | None = None,
        allowed_embed_domains: collections.abc.Collection[str] | None = None,
        models: collections.abc.Sequence[str] | None = None,
    ):
        self.looker_host = looker_host.strip()
        self.looker_secret = looker_secret
        self.allowed_dashboard_ids: frozenset[str] = frozenset(
            dashboard_id.strip()
            for dashboard_id in (allowed_dashboard_ids or ())
            if isinstance(dashboard_id, str) and dashboard_id.strip()
        )
        self.allowed_embed_domains: frozenset[str] = frozenset(
            normalized
            for domain in (allowed_embed_domains or ())
            if isinstance(domain, str)
            and (
                normalized := _normalize_origin(
                    domain.strip(), allow_root_slash=True
                )
            )
            is not None
        )
        self.models: list[str] = [
            model.strip()
            for model in (models or ())
            if isinstance(model, str) and model.strip()
        ]

    def _validate_embed_query(self, raw_query: str) -> list[tuple[str, str]]:
        """Validate allow-listed Looker Embed SDK query params inside `src`."""
        try:
            pairs = urllib.parse.parse_qsl(
                raw_query, keep_blank_values=True, strict_parsing=True
            )
        except ValueError as exc:
            raise errors.InvalidField("src") from exc

        seen_keys: set[str] = set()
        canonical_params: list[tuple[str, str]] = []
        for key, value in pairs:
            if key not in _ALLOWED_EMBED_QUERY_KEYS or key in seen_keys:
                raise errors.InvalidField("src")
            seen_keys.add(key)

            if key == "embed_domain":
                normalized_origin = _normalize_origin(value, allow_root_slash=False)
                if (
                    normalized_origin is None
                    or normalized_origin not in self.allowed_embed_domains
                ):
                    raise errors.InvalidField("src")
                canonical_params.append(("embed_domain", normalized_origin))
            elif key == "sdk":
                if not _SDK_VERSION_RE.fullmatch(value):
                    raise errors.InvalidField("src")
                canonical_params.append(("sdk", value))

        return canonical_params

    def _validate_and_canonicalize_src(
        self, query: datastructures.QueryParams
    ) -> str:
        """Validate `src` against configured allow-lists and rebuild canonically."""
        if (
            not self.looker_host
            or not self.looker_secret
            or not self.allowed_dashboard_ids
            or not _HOST_RE.fullmatch(self.looker_host)
        ):
            logger.error(
                "Looker SSO embed misconfigured: missing valid looker_host, "
                "looker_secret, or allowed_dashboard_ids."
            )
            raise errors.Forbidden()

        src_values = query.getlist("src")
        if len(src_values) != 1:
            raise errors.InvalidField("src")

        raw_src = src_values[0]
        if (
            not raw_src
            or raw_src != raw_src.strip()
            or _has_control_chars(raw_src)
            or "\\" in raw_src
            or raw_src.startswith("//")
            or ".." in raw_src
        ):
            raise errors.InvalidField("src")

        parsed = urllib.parse.urlsplit(raw_src)
        if (
            parsed.scheme
            or parsed.netloc
            or parsed.fragment
            or ("?" in raw_src and not parsed.query)
        ):
            raise errors.InvalidField("src")

        match = _DASHBOARD_PATH_RE.fullmatch(parsed.path)
        if not match or match.group(1) not in self.allowed_dashboard_ids:
            raise errors.InvalidField("src")

        canonical_path = f"/embed/dashboards/{match.group(1)}"
        if parsed.query:
            canonical_params = self._validate_embed_query(parsed.query)
            return f"{canonical_path}?{urllib.parse.urlencode(canonical_params)}"
        return canonical_path

    async def get_signed_url(
        self,
        user: UserModel,
        query: datastructures.QueryParams,
    ) -> str:
        """
        Generates signed url to access the dashboard.
        """
        canonical_src = self._validate_and_canonicalize_src(query)

        name = user.name.split(" ", maxsplit=1)
        first_name = name[0]
        last_name = name[1] if len(name) > 1 else None
        looker_user = User(
            external_user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            permissions=list(_MINIMAL_EMBED_PERMISSIONS),
            models_data=list(self.models),
            group_ids=[2],
            user_attributes={
                "group_ids": json.dumps(
                    [group.id for group in user.groups], cls=UUIDEncoder
                ),
                "organization_ids": json.dumps(
                    [org.id for org in user.organizations], cls=UUIDEncoder
                ),
                "state": user.state,
                "region": user.region,
                "county": getattr(user, "county", None),
            },
        )
        return "https://" + self._to_string(canonical_src, looker_user)

    def _sign(
        self, current_time: str, nonce: str, path: str, looker_user: User
    ) -> bytes:
        """
        Signs the data with google's expected pattern.
        """
        string_to_sign = "\n".join(
            [
                self.looker_host,
                path,
                nonce,
                current_time,
                looker_user.session_length,
                looker_user.external_user_id,
                looker_user.permissions,
                looker_user.models,
                looker_user.group_ids,
                looker_user.external_group_id,
                looker_user.user_attributes,
                looker_user.access_filters,
            ]
        )

        signer = hmac.new(
            bytearray(self.looker_secret, "UTF-8"), string_to_sign.encode("UTF-8"), sha1
        )
        return base64.b64encode(signer.digest())

    def _to_string(self, src: str, looker_user: User) -> str:
        """
        Gets all info and turns it into url
        """
        current_time = json.dumps(int(time.time()))
        nonce = json.dumps(uuid.uuid4().hex)
        path = "/login/embed/" + urllib.parse.quote_plus(src)
        signature = self._sign(current_time, nonce, path, looker_user)

        params = {
            "nonce": nonce,
            "time": current_time,
            "session_length": looker_user.session_length,
            "external_user_id": looker_user.external_user_id,
            "permissions": looker_user.permissions,
            "models": looker_user.models,
            "group_ids": looker_user.group_ids,
            "external_group_id": looker_user.external_group_id,
            "user_attributes": looker_user.user_attributes,
            "access_filters": looker_user.access_filters,
            "signature": signature.decode(),
            "first_name": looker_user.first_name,
            "last_name": looker_user.last_name,
            "force_logout_login": looker_user.force_logout_login,
        }
        query_string = "&".join(
            [f"{key}={urllib.parse.quote_plus(val)}" for key, val in params.items()]
        )

        return f"{self.looker_host}{path}?{query_string}"
