"""
Module to startup the server
"""

import alembic.config

from . import dependencies, factory

alembic_args = [
    "-c",
    "alembic.ini",
    "--raiseerr",
    "upgrade",
    "head",
]
alembic.config.main(argv=alembic_args)


app = factory.create_app(dependencies.create_container())
