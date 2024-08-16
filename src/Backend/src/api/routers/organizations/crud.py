"""
Module containing crud actions for organizations
"""

from api import models

from . import schemas


def update_org(
    organization: models.Organization,
    update_data: schemas.OrganizationCreate,
) -> models.Organization:
    """
    Abstraction of the update_org to use both in import and update
    """
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(organization, key, value)
    return organization
