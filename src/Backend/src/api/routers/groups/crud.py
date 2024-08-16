"""
Module containing crud actions for groups
"""

from api import models

from . import schemas


async def update_group(
    group: models.Group,
    update_data: schemas.GroupPatch,
) -> models.Group:
    """
    Abstraction of the update_group to use both in import and update
    """
    for key, value in update_data.dict().items():
        setattr(group, key, value)
    return group
