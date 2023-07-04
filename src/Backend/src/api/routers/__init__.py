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
Folder for all routers.
"""
from .auth.endpoints import router as auth_router
from .endpoints import router as base_router
from .exams.endpoints import router as exams_router
from .groups.endpoints import router as groups_router
from .organizations.endpoints import router as organizations_router
from .processor.endpoints import router as processor_router
from .roles.endpoints import router as roles_router
from .users.endpoints import router as users_router

__all__ = (
    "auth_router",
    "base_router",
    "exams_router",
    "groups_router",
    "organizations_router",
    "processor_router",
    "roles_router",
    "users_router",
)
