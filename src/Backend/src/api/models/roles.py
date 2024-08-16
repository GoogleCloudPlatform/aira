"""
Module used to build User structure.
"""

from __future__ import annotations

from sqlalchemy.orm import Mapped

from api import db


class Role(db.Base, db.DefaultColumns):
    """
    Role model.
    """

    __tablename__ = "roles"

    name: Mapped[db.Str100]

    display_name: Mapped[db.DictJSON]

    description: Mapped[db.DictJSON]

    scopes: Mapped[db.ListJSON]
