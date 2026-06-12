from fastapi import APIRouter


router = APIRouter(prefix="/dining-room", tags=["Dining Room"])


@router.get("/status")
def get_dining_room_status() -> dict:
    """
    Returns the basic status of the dining room module.

    This module will later manage dining room operations,
    waiters, table service, orders, table status and
    coordination with kitchen, bar and reception.
    """
    return {
        "module": "dining_room",
        "status": "active",
        "message": "Dining room module is running",
    }