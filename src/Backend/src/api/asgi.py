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
try:
    alembic.config.main(argv=alembic_args)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Alembic migration skipped in worker: {e}")


app = factory.create_app(dependencies.create_container())
