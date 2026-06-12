from fastapi import APIRouter


router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/status")
def get_security_status() -> dict:
    """
    Returns the basic status of the security module.

    This module will later manage hotel security,
    incidents, rounds, internal alerts, suspicious access
    and coordination with reception, maintenance and directors.
    """
    return {
        "module": "security",
        "status": "active",
        "message": "Security module is running",
    }