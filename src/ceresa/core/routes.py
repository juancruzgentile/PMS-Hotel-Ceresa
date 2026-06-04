from fastapi import APIRouter

from ceresa.core.module_loader import get_modules_status
from ceresa.core.settings import APP_NAME, APP_VERSION


router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
def system_health() -> dict:
    """
    Basic system health endpoint.

    Later this endpoint can include database status,
    active modules, external integrations and performance checks.
    """
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
    }


@router.get("/modules")
def system_modules() -> list[dict]:
    """
    Returns all configured modules and their current status.
    """
    return get_modules_status()