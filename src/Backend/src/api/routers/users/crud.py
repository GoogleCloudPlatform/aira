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
Module containing crud actions for users
"""
from passlib import context

from api import errors, models, ports

from . import schemas


async def create_user(
    body: schemas.UserCreate,
    uow: ports.UnitOfWork,
    hash_ctx: context.CryptContext,
    groups: list[models.Group],
    organizations: list[models.Organization],
) -> models.User:
    """
    Create user checking group_id logic.
    """
    body_dict = body.dict()
    password = body_dict.pop("password", None)
    user = models.User(**body_dict)

    user.groups = groups
    user.organizations = organizations
    match body.type:
        case models.UserType.PASSWORD if password:
            user.password = hash_ctx.hash(password)
        case models.UserType.PASSWORD if not password:
            raise errors.FieldNotNullable("password")
        case models.UserType.FIREBASE if password:
            raise errors.InvalidField("password")
    role = await uow.role_repository.get(role_id=user.role_id)
    user.role = role
    await validate_default_user(user)
    user_response = await uow.user_repository.create(user)
    return user_response


async def validate_default_user(user: models.User) -> None:
    """
    all checks to see if a user is compliant.
    """
    role = user.role
    groups = user.groups
    organizations = user.organizations
    if "admin" not in role.scopes:
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
