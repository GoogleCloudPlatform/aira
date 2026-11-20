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

    token: str = pydantic.Field(..., repr=False)


class EmailPasswordLogin(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    email_address: str
    password: pydantic.StrictStr = pydantic.Field(..., repr=False)


class Session(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    token_type: typing.Literal["bearer"] = "bearer"
    access_token: str = pydantic.Field(..., repr=False)
    refresh_token: str = pydantic.Field(..., repr=False)
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

    token: str = pydantic.Field(..., repr=False)
    password: pydantic.StrictStr = pydantic.Field(..., repr=False)
