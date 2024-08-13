"""
Base router.
"""

import logging

import fastapi

router = fastapi.APIRouter(tags=["utils"])

logger = logging.getLogger(__name__)


@router.get("/healthz")
def healthz() -> fastapi.Response:
    """
    Health check to see if it's able to receive more transactions.
    """
    logger.info("teste")
    return fastapi.Response(status_code=200, content="OK")
