from fastapi import APIRouter


router = APIRouter(prefix="/laundry", tags=["Laundry"])


@router.get("/status")
def get_laundry_status() -> dict:
    """
    Returns the basic status of the laundry module.

    This module will later manage hotel laundry operations,
    bed linen, towels, uniforms, washing cycles, clean deliveries
    and coordination with housekeeping.
    """
    return {
        "module": "laundry",
        "status": "active",
        "message": "Laundry module is running",
    }