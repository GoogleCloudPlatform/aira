"""
Sendgrid implementation.
"""

import typing

import aiohttp

from api import ports


class Sendgrid(ports.Notification):
    """
    Implementation for sendgrid notification
    """

    def __init__(self, api_key: str, sender_email: str):
        self.url = "https://api.sendgrid.com/v3/mail/send"
        self.key = api_key
        self.sender_email = sender_email

    async def send(self, email: str, template_file: str, **kwargs: typing.Any) -> bool:
        """
        Sends the notification
        """
        async with aiohttp.ClientSession() as session:
            body = {
                "from": {"email": self.sender_email},
                "personalizations": [
                    {
                        "to": [{"email": email}],
                        "dynamic_template_data": kwargs,
                    }
                ],
                "template_id": template_file,
            }
            async with session.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-type": "application/json",
                },
                json=body,
            ) as resp:
                resp.raise_for_status()
        return True
