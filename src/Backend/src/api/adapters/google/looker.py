"""
Module related to looker.
"""

import base64
import hmac
import json
import time
import typing
import urllib
import urllib.parse
import uuid
from hashlib import sha1

import looker_sdk
from looker_sdk.sdk.api40 import models as mdls
from starlette import datastructures

from api import ports
from api.helpers import UUIDEncoder
from api.models import User as UserModel


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

    user: User

    def __init__(self, looker_host: str, looker_secret: str):
        self.looker_host = looker_host
        self.looker_secret = looker_secret
        self._looker = looker_sdk.init40()

    async def get_signed_url(
        self,
        user: UserModel,
        query: datastructures.QueryParams,
    ) -> str:
        """
        Generates signed url to access the dashboard.
        """
        name = user.name.split(" ", maxsplit=1)
        first_name = name[0]
        last_name = name[1] if len(name) > 1 else None
        self.user = User(
            external_user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            permissions=[
                "access_data",
                "clear_cache_refresh",
                "download_without_limit",
                "mobile_app_access",
                "schedule_look_emails",
                "see_drill_overlay",
                "see_lookml_dashboards",
                "see_looks",
                "see_user_dashboards",
            ],
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
                "county": user.county,
            },
        )
        src = query.get("src", "")
        url = "https://" + self._to_string(src)
        return url

    def _sign(self, current_time: str, nonce: str, path: str) -> bytes:
        """
        Signs the data with google's expected pattern.
        """
        string_to_sign = "\n".join(
            [
                self.looker_host,
                path,
                nonce,
                current_time,
                self.user.session_length,
                self.user.external_user_id,
                self.user.permissions,
                self.user.models,
                self.user.group_ids,
                self.user.external_group_id,
                self.user.user_attributes,
                self.user.access_filters,
            ]
        )

        signer = hmac.new(
            bytearray(self.looker_secret, "UTF-8"), string_to_sign.encode("UTF-8"), sha1
        )
        return base64.b64encode(signer.digest())

    def _to_string(self, src: str) -> str:
        """
        Gets all info and turns it into url
        """
        current_time = json.dumps(int(time.time()))
        nonce = json.dumps(uuid.uuid4().hex)
        path = "/login/embed/" + urllib.parse.quote_plus(src)
        signature = self._sign(current_time, nonce, path)

        params = {
            "nonce": nonce,
            "time": current_time,
            "session_length": self.user.session_length,
            "external_user_id": self.user.external_user_id,
            "permissions": self.user.permissions,
            "models": self.user.models,
            "group_ids": self.user.group_ids,
            "external_group_id": self.user.external_group_id,
            "user_attributes": self.user.user_attributes,
            "access_filters": self.user.access_filters,
            "signature": signature.decode(),
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "force_logout_login": self.user.force_logout_login,
        }
        query_string = "&".join(
            [f"{key}={urllib.parse.quote_plus(val)}" for key, val in params.items()]
        )

        return f"{self.looker_host}{path}?{query_string}"

    async def delete_looker_user(self, user_id: str) -> str:
        """
        Delete Looker User by user id
        """
        # pylint: disable=arguments-differ
        return self._looker.delete_user(user_id)

    async def get_all_looker_users(self) -> typing.Sequence[mdls.User]:
        """
        Get a list of all Looker Users.
        """
        return self._looker.search_users(embed_user=True)
