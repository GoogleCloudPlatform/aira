import asyncio
import datetime
import os
import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sqlalchemy_aio
import injector
import fastapi
import typing
from httpx import AsyncClient


# Set test environment variable before imports
os.environ["_ENV"] = "local"

from api import db, ports, factory, typings, models
from api.typings import SessionFactory, Settings
from api.helpers import auth
from api.helpers.schemas import TokenData


# Mocks for tests
class MockStorage(ports.Storage):
    deleted_paths: list[str] = []

    def __init__(self, project_id: str, storage_path: str, creds_path: str):
        self.project_id = project_id
        self.storage_path = storage_path
        # Capture path in deletion
        mock_blob = lambda path: type("MockBlob", (), {"delete": lambda s: MockStorage.deleted_paths.append(path)})()
        mock_bucket = type(
            "MockBucket", (), {"blob": lambda s, path: mock_blob(path)}
        )()
        self.client = type(
            "MockClient", (), {"bucket": lambda s, name: mock_bucket}
        )()

    async def download(self, uri: str, file_name: str) -> str:
        path = f"/tmp/{file_name}"
        # Write minimal valid PDF bytes so pypdf doesn't crash
        minimal_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<< /Length 21 >>\nstream\nBT\n/F1 12 Tf\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000282 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n352\n%%EOF"
        with open(path, "wb") as f:
            f.write(minimal_pdf)
        return path

    async def upload_by_text(
        self, path: str, text: bytes, content_type: str | None = None
    ) -> str:
        return "mock-upload-id"

    async def upload_by_file(self, path: str, audio_path: str) -> str:
        return "mock-upload-id"

    async def generate_signed_url(
        self, path: str, mimetype: str, method: str = "PUT"
    ) -> str:
        return f"https://storage.googleapis.com/test-bucket/{path}?signed=true"

    async def get_blob_content_type(self, path: str) -> str | None:
        return "application/pdf"

    async def get_blob_size(self, path: str) -> int | None:
        return 100


class MockMessagePublisher(ports.MessagePublisher):

    def __init__(self) -> None:
        self.published = []

    async def publish(self, message: typings.Message, topic: str | None = None) -> None:
        self.published.append((message, topic))


# Injector Test Modules
class TestSQLAlchemyModule(injector.Module):

    def __init__(self, engine: sqlalchemy_aio.AsyncEngine):
        self.engine = engine

    @injector.provider
    @injector.singleton
    def provide_engine(self) -> sqlalchemy_aio.AsyncEngine:
        return self.engine

    @injector.provider
    @injector.singleton
    def provide_session_factory(
        self, engine: sqlalchemy_aio.AsyncEngine
    ) -> SessionFactory:
        return sqlalchemy_aio.async_sessionmaker(
            bind=engine, expire_on_commit=False, class_=sqlalchemy_aio.AsyncSession
        )


class MockGenAI(ports.GenAI):

    def __init__(self):
        self.deleted_doc_ids = []

    def generate_words(
        self,
        qty_words: str,
        question_type: models.QuestionType,
        block_words: list[str] | None = None,
    ) -> str:
        return "word"

    def generate_multiple_choice(
        self,
        qty: int,
        text: str | None,
        user_input: str | None,
        block_questions: list[str] | None = None,
    ) -> dict[str, typing.Any]:
        return {}

    def generate_text(self, subject: str = "infantil") -> str:
        return "text"

    def generate_question(
        self,
        question_type: models.QuestionType,
        text_data: str | None,
        user_input: str | None,
        block_questions: list[str],
        question_theme: models.QuestionTheme | None = None,
    ) -> str:
        return "question"

    def evaluate_test(
        self,
        question_type: models.QuestionType,
        text_data: str,
        tts_data: str,
        question_theme: models.QuestionTheme | None = None,
    ) -> tuple[bool, str]:
        return True, "correct"

    def get_exam_feedback(self, questions: list[typing.Any]) -> str:
        return "feedback"

    async def index_document(
        self, doc_id: str, text: str, metadata: dict[str, typing.Any] | None = None
    ) -> None:
        pass

    async def delete_document(self, doc_id: str) -> None:
        self.deleted_doc_ids.append(doc_id)

    async def query_kb(
        self, query_text: str, limit: int = 5
    ) -> list[dict[str, typing.Any]]:
        return []

    async def generate_description(self, text: str) -> str:
        return "Mocked AI description of the pedagogical file."


class TestGoogleModule(injector.Module):

    def __init__(self, publisher: MockMessagePublisher, gen_ai: MockGenAI):
        self.publisher = publisher
        self.gen_ai = gen_ai

    @injector.provider
    @injector.singleton
    def provide_pubsub(self) -> ports.MessagePublisher:
        return self.publisher

    @injector.provider
    @injector.singleton
    def provide_storage_factory(self) -> ports.StorageFactory:
        return lambda bucket_name: MockStorage(
            project_id="test", storage_path=bucket_name, creds_path=""
        )

    @injector.provider
    @injector.singleton
    def provide_generative_ai(self) -> ports.GenAI:
        return self.gen_ai




@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    db_uri = os.environ.get(
        "_DATABASE_TEST_URI",
        "postgresql+asyncpg://fabriciols@localhost:5432/aira_test",
    )
    engine = sqlalchemy_aio.create_async_engine(db_uri)

    # Drop and recreate tables to start fresh
    async with engine.begin() as conn:
        await conn.run_sync(db.Base.metadata.drop_all)
        await conn.run_sync(db.Base.metadata.create_all)

    yield engine
    await engine.dispose()



@pytest_asyncio.fixture
async def session_factory(db_engine):
    factory: SessionFactory = sqlalchemy_aio.async_sessionmaker(
        bind=db_engine, expire_on_commit=False, class_=sqlalchemy_aio.AsyncSession
    )
    yield factory


@pytest.fixture
def mock_publisher():
    return MockMessagePublisher()


@pytest.fixture
def mock_gen_ai():
    return MockGenAI()


@pytest_asyncio.fixture
async def test_app(db_engine, mock_publisher, mock_gen_ai):
    # Setup dependencies injection container with in-memory database
    from api.dependencies import (
        SettingsModule,
        SQLAlchemyModule,
        SyncModule,
        UtilModule,
        TracingModule,
    )

    settings = Settings(
        {
            "project_id": "test-project",
            "kb_bucket_path": "test-kb-bucket",
            "kb_processing_topic": "kb_processing_topic",
            "env": "local",
        }
    )

    class TestSettingsModule(injector.Module):

        @injector.multiprovider
        @injector.singleton
        def provide_settings(self) -> Settings:
            return settings

    modules = (
        TestSettingsModule(),
        TestSQLAlchemyModule(db_engine),
        SQLAlchemyModule(),
        SyncModule(),
        TestGoogleModule(mock_publisher, mock_gen_ai),
        UtilModule(),
        TracingModule(),
    )

    container = injector.Injector(modules)
    application = factory.create_app(container)

    yield application


@pytest_asyncio.fixture
async def client(test_app):
    # Override auth.get_token globally for API tests
    async def override_get_token():
        return TokenData(
            sub="00000000-0000-0000-0000-000000000000:0",
            aud="test-aud",
            exp=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=1),
            nbf=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=1),
            iat=datetime.datetime.now(datetime.timezone.utc),
            scopes=["admin"],
        )

    test_app.dependency_overrides[auth.get_token] = override_get_token

    async with AsyncClient(
        app=test_app, base_url="http://testserver"
    ) as async_client:
        yield async_client

    test_app.dependency_overrides.clear()
