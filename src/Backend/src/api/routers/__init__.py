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
