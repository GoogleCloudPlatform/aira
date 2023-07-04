"""
Module containing all modules to be instantiated
"""
import logging
import os

import fastapi
import fastapi_injector
import injector
from passlib import context
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from . import ports
from .adapters import google, memory
from .adapters.sqlalchemy import (
    exam,
    group,
    organization,
    role,
    session_query,
    unit_of_work,
    user,
)
from .helpers import auth, schemas, session_manager
from .typings import SessionFactory, Settings

logger = logging.getLogger(__name__)


class SettingsModule(injector.Module):
    """
    Module to contain just settings.
    """

    @injector.multiprovider
    @injector.singleton
    def provide_settings(self) -> Settings:
        """
        Provide settings from environment.
        """
        settings = {
            k[1:].lower(): v for k, v in os.environ.items() if k.startswith("_")
        }

        return Settings(settings)

    @injector.multiprovider
    @injector.singleton
    def provide_hashing_context(self) -> context.CryptContext:
        """
        Provide settings from environment.
        """
        ctx = context.CryptContext(schemes=["bcrypt"], deprecated="auto")

        return ctx


class EngineSQLAlchemy(injector.Module):
    """
    DBSQLAlchemy module.
    """

    @injector.provider
    @injector.singleton
    def provide_engine(self, settings: Settings) -> sqlalchemy_aio.AsyncEngine:
        """
        Provides sqlalchemy engine.
        """
        return sqlalchemy_aio.create_async_engine(settings.get("database_uri", ""))


class EngineTestSQLAlchemy(injector.Module):
    """
    EngineSQLAlchemy module.
    """

    @injector.provider
    @injector.singleton
    def provide_engine(self, settings: Settings) -> sqlalchemy_aio.AsyncEngine:
        """
        Provides sqlalchemy engine.
        """
        return sqlalchemy_aio.create_async_engine(settings.get("database_test_uri", ""))


class SQLAlchemyModule(injector.Module):  # pylint: disable=too-many-public-methods
    """
    SQLAlchemy module.
    """

    @injector.provider
    @injector.singleton
    def provide_session_factory(
        self, engine: sqlalchemy_aio.AsyncEngine
    ) -> SessionFactory:
        """
        Provides sqlalchemy session.
        """
        factory: SessionFactory = sqlalchemy_aio.async_sessionmaker(
            bind=engine, expire_on_commit=False, class_=sqlalchemy_aio.AsyncSession
        )
        return factory

    @injector.provider
    @injector.singleton
    def provide_uow_builder(
        self, session_factory: SessionFactory
    ) -> ports.UnitOfWorkBuilder:
        """
        Provides sqlalchemy session.
        """
        return unit_of_work.UnitOfWorkBuilder(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_get_session_query(
        self, session_factory: SessionFactory
    ) -> ports.GetSession:
        """
        Provides sqlalchemy session.
        """
        return session_query.GetSession(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_orgs(
        self, session_factory: SessionFactory
    ) -> ports.ListOrganizations:
        """
        Provides sqlalchemy list orgs.
        """
        return organization.ListOrganizations(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_get_org(self, session_factory: SessionFactory) -> ports.GetOrganization:
        """
        Provides sqlalchemy list groups.
        """
        return organization.GetOrganization(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_groups(self, session_factory: SessionFactory) -> ports.ListGroups:
        """
        Provides sqlalchemy list groups.
        """
        return group.ListGroups(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_get_group(self, session_factory: SessionFactory) -> ports.GetGroup:
        """
        Provides sqlalchemy list groups.
        """
        return group.GetGroup(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_users(self, session_factory: SessionFactory) -> ports.ListUsers:
        """
        Provides sqlalchemy list users.
        """
        return user.ListUsers(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_get_user(self, session_factory: SessionFactory) -> ports.GetUser:
        """
        Provides sqlalchemy get user.
        """
        return user.GetUser(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_roles(self, session_factory: SessionFactory) -> ports.ListRoles:
        """
        Provides sqlalchemy list users.
        """
        return role.ListRoles(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_get_role(self, session_factory: SessionFactory) -> ports.GetRole:
        """
        Provides sqlalchemy get user.
        """
        return role.GetRole(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_exams(self, session_factory: SessionFactory) -> ports.ListExams:
        """
        Provides sqlalchemy list users.
        """
        return exam.ListExams(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_get_exam(self, session_factory: SessionFactory) -> ports.GetExam:
        """
        Provides sqlalchemy get user.
        """
        return exam.GetExam(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_pending_exams(
        self, session_factory: SessionFactory
    ) -> ports.ListPendingExams:
        """
        Provides sqlalchemy get user.
        """
        return exam.ListPendingExams(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_pending_questions(
        self, session_factory: SessionFactory
    ) -> ports.ListPendingQuestions:
        """
        Provides sqlalchemy list pending questions.
        """
        return exam.ListPendingQuestions(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_get_pending_question(
        self, session_factory: SessionFactory
    ) -> ports.GetPendingQuestion:
        """
        Provides sqlalchemy get pending question.
        """
        return exam.GetPendingQuestion(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_get_exam_user_question_status(
        self, session_factory: SessionFactory
    ) -> ports.GetExamUserStatus:
        """
        Provides sqlalchemy get exam user.
        """
        return exam.GetExamUserStatus(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_groups_without_org(
        self, session_factory: SessionFactory
    ) -> ports.ListGroupsWithoutOrg:
        """
        Provides sqlalchemy get exam user.
        """
        return group.ListGroupsWithoutOrg(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_check_user_on_group(
        self, session_factory: SessionFactory
    ) -> ports.CheckUserOnGroup:
        """
        Provides sqlalchemy get exam user.
        """
        return user.CheckUserOnGroup(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_check_group_on_org(
        self, session_factory: SessionFactory
    ) -> ports.CheckGroupOnOrg:
        """
        Provides sqlalchemy CheckGroupOnOrg.
        """
        return group.CheckGroupOnOrg(
            session_factory=session_factory,
        )

    @injector.provider
    @injector.singleton
    def provide_list_question_with_status(
        self, session_factory: SessionFactory
    ) -> ports.ListQuestionsWithStatus:
        """
        Provides sqlalchemy ListQuestionsWithStatus.
        """
        return exam.ListQuestionsWithStatus(
            session_factory=session_factory,
        )


class MemoryModule(injector.Module):
    """
    Google module.
    """

    @injector.provider
    @injector.singleton
    def provide_secret_manager(self) -> ports.SecretManager:
        """
        Provide the Memory's Secret Manager.
        """
        return memory.SecretManager()

    @injector.provider
    @injector.singleton
    def provide_external_auth(self) -> ports.ExternalAuth:
        """
        Provide the Memory's External Auth.
        """
        return memory.ExternalAuth()


class GoogleModule(injector.Module):
    """
    Google module.
    """

    @injector.provider
    @injector.singleton
    def provide_cloud_storage(self, settings: Settings) -> ports.Storage:
        """
        Provide the Cloud Storage.
        """
        return google.CloudStorage(
            project_id=settings.get("project_id", ""),
            storage_path=settings.get("bucket_path", ""),
            creds_path=settings.get("gcp_storage_credentials", ""),
        )

    @injector.provider
    @injector.singleton
    def provide_speech_to_text(
        self, settings: Settings, storage: ports.Storage
    ) -> ports.SpeechToText:
        """
        Provide the Cloud Speech to Text.
        """
        return google.SpeechToText(
            project_id=settings.get("project_id", ""),
            creds_path=settings.get("gcp_stt_credentials", ""),
            storage=storage,
        )

    @injector.provider
    @injector.singleton
    def provide_secret_manager(self, settings: Settings) -> ports.SecretManager:
        """
        Provide the GCP's Secret Manager.
        """
        return google.SecretManager(
            project_id=settings.get("project_id", ""),
            creds_path=settings.get("gcp_sm_credentials", ""),
        )

    @injector.provider
    @injector.singleton
    def provice_firebase_auth(self, settings: Settings) -> ports.ExternalAuth:
        """
        Provide the GCP's Secret Manager.
        """
        return google.FirebaseAuth(
            project_id=settings.get("project_id", ""),
            creds_path=settings.get("gcp_fb_credentials", ""),
        )

    @injector.provider
    @injector.singleton
    def provide_pubsub(self, settings: Settings) -> ports.MessagePublisher:
        """
        Provide the GCP's Pubsub.
        """
        return google.MessagePublisher(
            project_id=settings.get("project_id", ""),
            creds_path=settings.get("gcp_bucket_credentials", ""),
            topic=settings.get("pubsub_topic", ""),
        )

    @injector.provider
    @injector.singleton
    def provide_bigquery(self, settings: Settings) -> ports.AnalyticalResult:
        """
        Provide the GCP's BigQuery.
        """
        return google.BigQuery(
            project_id=settings.get("project_id", ""),
            dataset=settings.get("bq_dataset", ""),
            table_name=settings.get("bq_table_name", ""),
            creds_path=settings.get("gcp_bigquery_credentials", ""),
        )

    @injector.provider
    @injector.singleton
    def provide_looker(self, settings: Settings) -> ports.Dashboard:
        """
        Provide the GCP's Looker.
        """
        return google.LookerDashboard(
            looker_secret=settings.get("looker_secret", ""),
            looker_host=settings.get("looker_host", ""),
        )


def create_container() -> injector.Injector:
    """
    Create the dependency injection container.

    :return: configured dependency injection container.
    """
    modules = (
        SettingsModule(),
        EngineSQLAlchemy(),
        SQLAlchemyModule(),
        GoogleModule(),
    )

    return injector.Injector(modules)


def get_session_manager(
    get_session_query: ports.GetSession = fastapi_injector.Injected(ports.GetSession),
    token_data: schemas.TokenData = fastapi.Security(auth.get_token),
) -> session_manager.SessionManager:
    """
    Get the session_manager.
    """
    return session_manager.SessionManager(
        token_data=token_data, get_session_query=get_session_query
    )
