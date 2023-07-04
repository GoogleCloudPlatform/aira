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
Configurations for tests.
"""
# pylint: disable=unused-argument,redefined-outer-name

import asyncio
import datetime
import logging
import pathlib
import typing
import unittest.mock
import uuid

import alembic.command
import hypothesis
import pytest
import pytest_asyncio
import sqlalchemy as sa
from alembic import config
from google.cloud.speech_v1p1beta1.types import (
    SpeechRecognitionAlternative,
    SpeechRecognitionResult,
    WordInfo,
)
from passlib import context
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import models
from api.adapters.google import BigQuery, CloudStorage, SpeechToText
from api.helpers import time_now, util
from tests.helpers.database import create_test_container

logger = logging.getLogger(__name__)

hypothesis.settings.register_profile(
    "fast",
    hypothesis.settings(
        max_examples=10,
        deadline=datetime.timedelta(milliseconds=3000),
        print_blob=True,
    ),
)

hypothesis.settings.load_profile("fast")


@pytest.fixture
def hash_ctx() -> context.CryptContext:
    """
    Patching credentials.
    """
    ctx = context.CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx


@pytest.fixture
def engine_factory_mock() -> typing.Any:
    """
    Patching credentials.
    """
    create_engine = unittest.mock.Mock()
    with unittest.mock.patch(
        "sqlalchemy.ext.asyncio.create_async_engine",
        create_engine,
    ):
        yield create_engine


@pytest.fixture(autouse=True)
def credentials(request: pytest.FixtureRequest) -> typing.Any:
    """
    Patching credentials.
    """
    if "disable_autouse" in request.keywords:
        yield
    else:
        creds = unittest.mock.Mock()
        with unittest.mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            creds,
        ):
            yield creds


@pytest.fixture(autouse=True)
def fb_credentials(request: pytest.FixtureRequest) -> typing.Any:
    """
    Patching credentials.
    """
    if "disable_autouse" in request.keywords:
        yield
    else:
        creds = unittest.mock.Mock()
        with unittest.mock.patch(
            "firebase_admin.credentials.Certificate",
            creds,
        ):
            yield creds


@pytest.fixture
def storage_client() -> typing.Generator[unittest.mock.Mock, None, None]:
    """
    Patching cloud storage client.
    """
    client = unittest.mock.Mock()
    with unittest.mock.patch("google.cloud.storage.Client", client):
        client.return_value.bucket.return_value = unittest.mock.Mock()
        client.return_value.bucket.return_value.blob.return_value = unittest.mock.Mock()
        client.return_value.bucket.return_value.blob.return_value.id = "test/test/test"
        # pylint: disable=line-too-long
        client.return_value.bucket.return_value.blob.return_value.generate_signed_url.return_value = (
            "https://storage.googleapis.com/test"
        )
        yield client


@pytest.fixture
def cloud_storage(
    storage_client: unittest.mock.Mock,
    credentials: unittest.mock.Mock,
) -> CloudStorage:
    """
    Instantiating cloud storage with patched client.
    """
    return CloudStorage(project_id="", creds_path="", storage_path="")


@pytest.fixture
def stt_client() -> typing.Generator[unittest.mock.AsyncMock, None, None]:
    """
    Patching speech to text client.
    """
    client = unittest.mock.AsyncMock()
    operation = unittest.mock.AsyncMock()
    client.return_value.long_running_recognize.return_value = operation
    response = unittest.mock.Mock()
    operation.result.return_value = response
    results = [
        SpeechRecognitionResult(
            alternatives=[
                SpeechRecognitionAlternative(
                    transcript="blabla",
                    words=[WordInfo(start_time="0s", end_time="60s", word="test")],
                )
            ]
        )
    ]
    response.results = [results]
    with unittest.mock.patch(
        "google.cloud.speech_v1p1beta1.services.speech.async_client.SpeechAsyncClient",
        client,
    ):
        yield client


@pytest.fixture
def secret_manager_client() -> typing.Any:
    """
    Patching secret_manager client.
    """
    client = unittest.mock.Mock()
    with unittest.mock.patch(
        "google.cloud.secretmanager_v1beta1.SecretManagerServiceAsyncClient",
        client,
    ):
        yield client


@pytest.fixture
def firebase_auth_client() -> typing.Any:
    """
    Patching firebase auth client.
    """
    client = unittest.mock.Mock()
    with unittest.mock.patch(
        "firebase_admin.initialize_app",
        client,
    ):
        yield client


@pytest.fixture
def cloud_stt(
    stt_client: unittest.mock.Mock,
    credentials: unittest.mock.Mock,
    cloud_storage: CloudStorage,
) -> SpeechToText:
    """
    Instantiating cloud stt with patched client.
    """
    return SpeechToText(project_id="", creds_path="...", storage=cloud_storage)


@pytest.fixture
def bigquery_client() -> typing.Generator[unittest.mock.Mock, None, None]:
    """
    Patching cloud bigquery client.
    """
    client = unittest.mock.Mock()
    with unittest.mock.patch("google.cloud.bigquery.Client", client):
        yield client


@pytest.fixture
def bigquery(
    bigquery_client: unittest.mock.Mock,
    credentials: unittest.mock.Mock,
) -> BigQuery:
    """
    Instantiating bigquery with patched client.
    """
    return BigQuery(project_id="", dataset="", table_name="", creds_path="")


@pytest.fixture
def fake_org() -> models.Organization:
    """
    Instantiating a fake org
    """
    org_model = models.Organization(
        city="fake-city",
        state="RJ",
        name="fake-org",
        customer_id="fake",
        region="fake-region",
    )
    org_model.created_at = org_model.updated_at = util.time_now()
    return org_model


@pytest.fixture
def fake_group(fake_org: models.Organization) -> models.Group:
    """
    Instantiating a fake group
    """
    group_model = models.Group(
        grade=models.Grades.FIRST_FUND,
        customer_id="fake",
        shift="morning",
        name="fake-group",
        organization_id=fake_org.id,
    )
    group_model.created_at = group_model.updated_at = util.time_now()
    group_model.organization = fake_org
    return group_model


@pytest.fixture
def fake_role() -> models.Role:
    """
    Instantiating a fake role
    """
    role_model = models.Role(
        scopes=["fake-role"],
        name="admin",
        display_name={},
        description={},
    )
    return role_model


@pytest.fixture
def fake_user(fake_role: models.Role, fake_group: models.Group) -> models.User:
    """
    Instantiating a fake user
    """
    user_model = models.User(
        external_id="test-user",
        customer_id="fake",
        type=models.users.UserType.FIREBASE,
        email_address="test@example.com",
        name="Test User",
        groups=[fake_group],
        role_id=fake_role.id,
        organizations=[],
    )
    user_model.role = fake_role
    return user_model


@pytest.fixture
def fake_session(fake_user: models.User) -> models.Session:
    """
    Instantiating a fake user
    """
    session_model = models.Session(
        user_id=fake_user.id,
        expires_at=time_now() + datetime.timedelta(days=1),
        generation=1,
        id=uuid.uuid4(),
    )
    session_model.user = fake_user
    return session_model


@pytest.fixture
def fake_exam() -> models.Exam:
    """
    Instantiating a fake exam
    """
    exam_model = models.Exam(
        name="fake",
        start_date=util.time_now(),
        end_date=util.time_now() + datetime.timedelta(days=30),
        questions=[],
        grade=models.Grades.FIRST_FUND,
    )
    return exam_model


@pytest.fixture
def fake_user_session(fake_user: models.User) -> models.Session:
    """
    Instantiating a fake user
    """
    session_model = models.Session(
        id=uuid.uuid4(),
        expires_at=util.time_now(),
        generation=1,
        user_id=fake_user.id,
    )
    session_model.user = fake_user
    session_model.user.role.scopes = ["user"]
    return session_model


@pytest.fixture(scope="session")
def event_loop() -> typing.Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Getting event loop for async fixtures.
    """
    loop = asyncio.get_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_db(request: pytest.FixtureRequest) -> None:
    """
    Run alembic to run migrations.
    """
    if "disable_db" in request.keywords:
        return
    container = create_test_container()
    engine = container.get(sqlalchemy_aio.AsyncEngine)
    alembic_config = config.Config(
        str(pathlib.Path(__file__).parent.parent / "alembic.ini"),
        attributes={"skip_logger_setup": True},
    )
    async with engine.connect() as conn:
        await conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        await conn.execute(sa.text("CREATE SCHEMA public"))
        await conn.commit()
    alembic.command.upgrade(alembic_config, "head")
