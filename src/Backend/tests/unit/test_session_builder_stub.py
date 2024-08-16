"""
Unit test for session memory implementation.
"""

import pytest
from api.adapters.memory import unit_of_work


@pytest.mark.asyncio
async def test_it_should_create_session() -> None:
    """
    it should create session memory implementation
    """
    uow_builder = unit_of_work.UnitOfWorkBuilder()
    async with uow_builder() as uow:
        assert uow.closed is False
        assert isinstance(uow, unit_of_work.UnitOfWork)
    assert uow.closed is True
