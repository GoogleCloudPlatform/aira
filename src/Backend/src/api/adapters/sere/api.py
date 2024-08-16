import typing

import aiohttp

from api import ports


class SereApi(ports.DataSyncApi):
    def __init__(self, api_key: str) -> None:
        self.base_url = "https://api.seed.pr.gov.br/lia"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "ApiKey": f"{api_key}",
        }

    async def get_list(
        self, session: aiohttp.ClientSession, endpoint: str, nre: int
    ) -> typing.Any:
        async with session.get(
            f"{self.base_url}/{endpoint}/{nre}",
            headers=self.headers,
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def list_group(self) -> list[dict[str, typing.Any]]:
        groups: list[typing.Any] = []
        async with aiohttp.ClientSession() as session:
            for nre in range(1, 33):
                groups.extend(await self.get_list(session, "turma", nre))
        return groups

    async def list_organization(self) -> list[dict[str, typing.Any]]:
        organizations: list[typing.Any] = []
        async with aiohttp.ClientSession() as session:
            for nre in range(1, 33):
                organizations.extend(await self.get_list(session, "escola", nre))
        return organizations

    async def list_student(self) -> list[dict[str, typing.Any]]:
        students: list[typing.Any] = []
        async with aiohttp.ClientSession() as session:
            for nre in range(1, 33):
                students.extend(await self.get_list(session, "matricula", nre))
        return students

    async def list_student_paginated(self, index: int) -> typing.Any:
        async with aiohttp.ClientSession() as session:
            return await self.get_list(session, "matricula", index)

    async def list_professor(self) -> list[dict[str, typing.Any]]:
        professors: list[typing.Any] = []
        async with aiohttp.ClientSession() as session:
            for nre in range(1, 33):
                professors.extend(await self.get_list(session, "professor", nre))
        return professors
