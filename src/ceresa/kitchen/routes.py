from fastapi import APIRouter


router = APIRouter(prefix="/kitchen", tags=["Kitchen"])


@router.get("/status")
def get_kitchen_status() -> dict:
    """
    Returns the basic status of the kitchen module.

    This module will later manage kitchen operations,
    meal preparation, guest food requests, allergies,
    stock coordination and communication with sala.
    """
    return {
        "module": "kitchen",
        "status": "active",
        "message": "Kitchen module is running",
    }