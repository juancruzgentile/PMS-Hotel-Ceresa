from fastapi import APIRouter


router = APIRouter(prefix="/beach", tags=["Beach"])


@router.get("/status")
def get_beach_status() -> dict:
    """
    Returns the basic status of the beach module.

    This module will later manage beach services,
    umbrellas, sunbeds, guest reservations, beach zones
    and coordination with reception, leisure, transport,
    security and maintenance.
    """
    return {
        "module": "beach",
        "status": "active",
        "message": "Beach module is running",
    }