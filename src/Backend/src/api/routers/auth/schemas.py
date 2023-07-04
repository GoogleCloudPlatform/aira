"""
Module containing schemas for all auth endpoints
"""
import datetime
import typing
import uuid

import pydantic


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
    password: str


class Session(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    id: uuid.UUID
    user_name: str
    token_type: typing.Literal["bearer"] = "bearer"
    access_token: str
    refresh_token: str
    expires_in: datetime.timedelta
    scopes: list[str]
