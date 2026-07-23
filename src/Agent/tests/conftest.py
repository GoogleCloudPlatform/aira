import pytest
from unittest.mock import MagicMock
from google.adk.tools.tool_context import ToolContext

@pytest.fixture
def mock_tool_context_teacher():
    """Returns a mock ToolContext representing a logged-in teacher."""
    context = MagicMock(spec=ToolContext)
    context.state = {
        "user_email": "professor@radhark.tech",
        "user_name": "Teste Professor",
        "role_name": "teacher",
        "allowed_organizations": ["school-uuid-123"],
        "allowed_organization_names": ["Escola Senai"],
        "allowed_groups": ["class-uuid-456"]
    }
    return context

@pytest.fixture
def mock_tool_context_admin():
    """Returns a mock ToolContext representing a logged-in administrator."""
    context = MagicMock(spec=ToolContext)
    context.state = {
        "user_email": "admin@radhark.tech",
        "user_name": "Teste Admin",
        "role_name": "admin",
        "allowed_organizations": [],
        "allowed_organization_names": [],
        "allowed_groups": []
    }
    return context

@pytest.fixture
def mock_tool_context_unauthenticated():
    """Returns a mock ToolContext representing an unauthenticated session."""
    context = MagicMock(spec=ToolContext)
    context.state = {}
    return context
