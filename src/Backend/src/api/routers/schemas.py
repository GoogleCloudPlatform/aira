"""
Module that contains all common schemas to the routers.
"""

import pydantic


class PubsubMessage(pydantic.BaseModel, extra=pydantic.Extra.allow):
    """
    Defines required pubsub message.
    """

    data: bytes
    message_id: str = pydantic.Field(alias="messageId")


class PubsubRequest(pydantic.BaseModel, extra=pydantic.Extra.allow):
    """
    Defines required pubsub request.
    """

    message: PubsubMessage
    subscription: str
