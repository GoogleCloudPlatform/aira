"""
Base router.
"""
import fastapi

router = fastapi.APIRouter()


@router.get("/healthz")
def healthz() -> fastapi.Response:
    """
    Health check to see if it's able to receive more transactions.
    """
    return fastapi.Response(status_code=200, content="OK")
