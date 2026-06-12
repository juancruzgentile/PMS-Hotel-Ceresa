from fastapi import APIRouter


router = APIRouter(prefix="/guests", tags=["Guests"])


@router.get("/status")
def get_guests_status() -> dict:
    """
    Returns the basic status of the guests module.

    This module will later manage hotel guests,
    guest profiles, guest history, contact information,
    stay-related data and coordination with reservations,
    reception, billing, transport and hotel services.
    """
    return {
        "module": "guests",
        "status": "active",
        "message": "Guests module is running",
    }