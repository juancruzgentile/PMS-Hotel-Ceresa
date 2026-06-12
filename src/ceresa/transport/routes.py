from fastapi import APIRouter


router = APIRouter(prefix="/transport", tags=["Transport"])


@router.get("/status")
def get_transport_status() -> dict:
    """
    Returns the basic status of the transport module.

    This module will later manage guest transfers,
    drivers, pickup requests, trip status, GPS location
    with explicit permissions and coordination with reception.
    """
    return {
        "module": "transport",
        "status": "active",
        "message": "Transport module is running",
    }