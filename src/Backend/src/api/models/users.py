"""
Module used to build User structure.
"""
from __future__ import annotations

import datetime
import enum

import sqlalchemy as sa
from passlib import context
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api import db

from . import groups, organizations
from .roles import Role


class UserType(enum.StrEnum):
    """
    User available types.
    """

    PASSWORD = "password"
    FIREBASE = "firebase"


class UserGroup(db.Base):
    """
    User Group model.
    """

    __tablename__ = "users_groups"

    user_id: Mapped[db.UuidPk] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    group_id: Mapped[db.UuidPk] = mapped_column(
        sa.ForeignKey("groups.id", ondelete="CASCADE")
    )

    created_at: Mapped[db.DateTime] = mapped_column(
        init=False, default=datetime.datetime.now(tz=datetime.UTC)
    )

    updated_at: Mapped[db.DateTime] = mapped_column(
        init=False,
        default=datetime.datetime.now(tz=datetime.UTC),
        onupdate=datetime.datetime.now(tz=datetime.UTC),
    )


class UserOrganization(db.Base):
    """
    User Organization model.
    """

    __tablename__ = "users_organizations"

    user_id: Mapped[db.UuidPk] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    organization_id: Mapped[db.UuidPk] = mapped_column(
        sa.ForeignKey("organizations.id", ondelete="CASCADE")
    )

    created_at: Mapped[db.DateTime] = mapped_column(
        init=False, default=datetime.datetime.now(tz=datetime.UTC)
    )

    updated_at: Mapped[db.DateTime] = mapped_column(
        init=False,
        default=datetime.datetime.now(tz=datetime.UTC),
        onupdate=datetime.datetime.now(tz=datetime.UTC),
    )


class User(db.Base, db.DefaultColumns):
    """
    User model.
    """

    __tablename__ = "users"

    external_id: Mapped[db.Str100 | None] = mapped_column(
        sa.String(100), unique=True, nullable=True
    )

    customer_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)

    type: Mapped[UserType]

    role_id: Mapped[db.UuidDefault] = mapped_column(
        sa.ForeignKey("roles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    name: Mapped[db.Str50]

    email_address: Mapped[db.Str100] = mapped_column(sa.String(100), unique=True)

    password: Mapped[str | None] = mapped_column(
        sa.String(100), nullable=True, init=False
    )

    last_login: Mapped[db.DateTime] = mapped_column(init=False, nullable=True)

    groups: Mapped[list[groups.Group]] = relationship(
        groups.Group,
        secondary=UserGroup.__table__,
        lazy="joined",
    )

    organizations: Mapped[list[organizations.Organization]] = relationship(
        organizations.Organization,
        secondary=UserOrganization.__table__,
        lazy="joined",
    )

    role: Mapped[Role] = relationship(
        "Role",
        init=False,
        lazy="joined",
    )

    def check_password(self, password: str, hash_ctx: context.CryptContext) -> bool:
        """
        Check if the password is valid.

        :param password: Password to be checked.
        :return: True if the password is valid, False otherwise.
        """
        valid, new_password = hash_ctx.verify_and_update(password, self.password)
        if valid and new_password:
            self.password = new_password
        return valid
