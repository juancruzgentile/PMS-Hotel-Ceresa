from fastapi import APIRouter


router = APIRouter(prefix="/reception", tags=["Reception"])


@router.get("/status")
def get_reception_status() -> dict:
    """
    Returns the basic status of the reception module.

    This module will later manage check-in, check-out,
    guest requests, room assignment and coordination
    with other hotel sectors.
    """
    return {
        "module": "reception",
        "status": "active",
        "message": "Reception module is running",
    }