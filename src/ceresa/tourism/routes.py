from fastapi import APIRouter


router = APIRouter(prefix="/tourism", tags=["Tourism"])


@router.get("/status")
def get_tourism_status() -> dict:
    """
    Returns the basic status of the tourism module.

    This module will later manage tourist activities,
    excursions, external reservations, guest recommendations
    and coordination with reception and transport.
    """
    return {
        "module": "tourism",
        "status": "active",
        "message": "Tourism module is running",
    }