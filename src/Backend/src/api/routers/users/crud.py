"""
Module containing crud actions for users
"""

import typing

from passlib import context

from api import errors, models


async def create_user(
    body_dict: dict[str, typing.Any],
    role: models.Role,
    hash_ctx: context.CryptContext,
    groups: list[models.Group],
    organizations: list[models.Organization],
) -> models.User:
    """
    Create user checking group_id logic.
    """
    _id = body_dict.pop("id", None)
    password = body_dict.pop("password", None)
    user = models.User(**body_dict)
    user.id = _id if _id else user.id

    user.groups = groups
    user.organizations = organizations

    match body_dict.get("type"):
        case models.UserType.PASSWORD | "password" if password:
            user.set_password(password, hash_ctx)
        case models.UserType.PASSWORD | "password" if not password:
            raise errors.FieldNotNullable("password")
        case models.UserType.FIREBASE | "firebase" if password:
            raise errors.InvalidField("password")
    user.role = role
    await validate_default_user(user)
    return user


async def validate_default_user(user: models.User) -> None:
    """
    all checks to see if a user is compliant.
    """
    role = user.role
    groups = user.groups
    organizations = user.organizations
    if "dashboard.viewer" not in role.scopes and "admin" not in role.scopes:
        if not groups:
            raise errors.FieldNotNullable("groups")
        if not organizations:
            raise errors.FieldNotNullable("organizations")
        if "user" in role.scopes:
            if len(groups) > 1:
                raise errors.InvalidGroupOrg("groups")
            if len(organizations) > 1:
                raise errors.InvalidGroupOrg("organizations")
    org_ids = [org.id for org in organizations]
    if groups is not None and not all(
        None if group.organization_id not in org_ids else group for group in groups
    ):
        raise errors.InvalidChosenGroup()


async def update_user(
    user: models.User,
    body_dict: dict[str, typing.Any],
    group_list: list[models.Group],
    org_list: list[models.Organization],
) -> models.User:
    """
    Abstraction of the update_user to use both in import and update
    """
    group_ids = [group.id for group in user.groups]
    org_ids = [organization.id for organization in user.organizations]
    for key, value in body_dict.items():
        if key == "groups":
            user.groups = [group for group in user.groups if group.id in value]
            groups = [group for group in value if group not in group_ids]
            group_ext = [group for group in group_list if group.id in groups]
            if group_ext:
                user.groups.extend(group_ext)
        elif key == "organizations":
            user.organizations = [
                organization
                for organization in user.organizations
                if organization.id in value
            ]
            organizations = [
                organization for organization in value if organization not in org_ids
            ]
            org_ext = [org for org in org_list if org.id in organizations]
            if organizations:
                user.organizations.extend(org_ext)
        else:
            setattr(user, key, value)
    await validate_default_user(user)
    return user
