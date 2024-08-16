"""
Module containing schemas for all auth endpoints
"""

import dataclasses
import datetime
import typing
import uuid

import pydantic

from api import typings


class FirebaseLogin(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    token: str


class EmailPasswordLogin(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    email_address: str
    password: pydantic.StrictStr


class Session(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    token_type: typing.Literal["bearer"] = "bearer"
    access_token: str
    refresh_token: str
    expires_in: datetime.timedelta
    scopes: list[str]


class ForgotPassword(pydantic.BaseModel):
    """
    Schema related to forgotten passwords.
    """

    email: pydantic.EmailStr


class ResetPassword(pydantic.BaseModel):
    """
    Schema related to resetting passwords.
    """

    token: str
    password: pydantic.StrictStr


@dataclasses.dataclass
class DeleteLookerUserMessage(typings.Message):
    """
    Dataclass to delete looker user.
    """

    user_id: str


class PubsubDeleteUserData(pydantic.BaseModel, extra=pydantic.Extra.allow):
    """
    Defines only needed data that will be converted from pubsub.
    """

    user_id: str
