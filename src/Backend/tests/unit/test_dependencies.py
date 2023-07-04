# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Module related to creation of the container.
"""
# pylint: disable=unused-argument
import unittest.mock

import injector
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import dependencies, ports, typings
from api.adapters import google
from api.adapters.sqlalchemy import unit_of_work


def test_create_container() -> None:
    """
    it should create the container properly.
    """
    container = dependencies.create_container()
    assert isinstance(container, injector.Injector)


def test_proper_setup_settings() -> None:
    """
    it should setup settings properly.
    """

    container = dependencies.create_container()

    settings = container.get(typings.Settings)

    assert isinstance(settings, dict)


def test_proper_setup_sqlalchemy_session_factory(
    engine_factory_mock: unittest.mock.Mock,
) -> None:
    """
    it should setup sqlalchemy session factory.
    """

    container = dependencies.create_container()

    session_factory = container.get(typings.SessionFactory)

    assert isinstance(session_factory, sqlalchemy_aio.async_sessionmaker)


def test_proper_setup_sqlalchemy_uow_builder(
    engine_factory_mock: unittest.mock.Mock,
) -> None:
    """
    it should setup sqlalchemy session builder.
    """

    container = dependencies.create_container()

    uow_builder = container.get(ports.UnitOfWorkBuilder)

    assert isinstance(uow_builder, unit_of_work.UnitOfWorkBuilder)


def test_proper_setup_google_cloud_storage(
    storage_client: unittest.mock.Mock,
) -> None:
    """
    it should setup google cloud storage.
    """

    container = dependencies.create_container()

    cloud_storage = container.get(ports.Storage)

    assert isinstance(cloud_storage, google.CloudStorage)


def test_proper_setup_secret_manager(
    secret_manager_client: unittest.mock.AsyncMock,
) -> None:
    """
    it should setup google secret_manager.
    """

    container = dependencies.create_container()

    secret_manager = container.get(ports.SecretManager)

    assert isinstance(secret_manager, google.SecretManager)


def test_proper_setup_firebase_auth(firebase_auth_client: unittest.mock.Mock) -> None:
    """
    it should setup firebase auth.
    """

    container = dependencies.create_container()

    external_auth = container.get(ports.ExternalAuth)

    assert isinstance(external_auth, google.FirebaseAuth)
