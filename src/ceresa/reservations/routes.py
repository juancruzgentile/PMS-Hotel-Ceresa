from fastapi import APIRouter


router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.get("/status")
def get_reservations_status() -> dict:
    """
    Returns the basic status of the reservations module.

    This module will later manage hotel reservations,
    booking dates, guest stays, room assignment,
    reservation status and coordination with guests,
    rooms, reception and billing.
    """
    return {
        "module": "reservations",
        "status": "active",
        "message": "Reservations module is running",
    }