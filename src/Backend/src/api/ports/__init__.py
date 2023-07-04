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
Folder containing all abstract classes.
"""
from .analytical import AnalyticalResult
from .auth import ExternalAuth
from .dashboard import Dashboard
from .exam import (
    ExamRepository,
    GetExam,
    GetExamUserStatus,
    GetPendingQuestion,
    ListExams,
    ListPendingExams,
    ListPendingQuestions,
    ListQuestionsWithStatus,
    QuestionRepository,
)
from .group import (
    CheckGroupOnOrg,
    GetGroup,
    GroupRepository,
    ListGroups,
    ListGroupsWithoutOrg,
)
from .message_publisher import MessagePublisher
from .organization import GetOrganization, ListOrganizations, OrganizationRepository
from .result import ResultRepository
from .role import GetRole, GetRoleByName, ListRoles, RoleRepository
from .secret_manager import SecretManager, Secrets
from .session_query import GetSession, SessionRepository
from .speech import SpeechToText
from .storage import Storage
from .unit_of_work import UnitOfWork, UnitOfWorkBuilder
from .user import CheckUserOnGroup, GetUser, ListUsers, UserRepository

__all__ = (
    "AnalyticalResult",
    "CheckGroupOnOrg",
    "CheckUserOnGroup",
    "Dashboard",
    "ExamRepository",
    "ExternalAuth",
    "GetExam",
    "GetExamUserStatus",
    "GetGroup",
    "GetOrganization",
    "GetPendingQuestion",
    "GetRoleByName",
    "GetRole",
    "GetSession",
    "GetUser",
    "GroupRepository",
    "ListExams",
    "ListGroups",
    "ListGroupsWithoutOrg",
    "ListOrganizations",
    "ListPendingExams",
    "ListPendingQuestions",
    "ListQuestionsWithStatus",
    "ListRoles",
    "ListUsers",
    "MessagePublisher",
    "OrganizationRepository",
    "ResultRepository",
    "RoleRepository",
    "SpeechToText",
    "Storage",
    "SecretManager",
    "Secrets",
    "UnitOfWork",
    "UnitOfWorkBuilder",
    "QuestionRepository",
    "SessionRepository",
    "UserRepository",
)
