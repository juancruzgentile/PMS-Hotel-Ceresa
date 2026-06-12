from fastapi import APIRouter


router = APIRouter(prefix="/leisure", tags=["Leisure"])


@router.get("/status")
def get_leisure_status() -> dict:
    """
    Returns the basic status of the leisure module.

    This module will later manage hotel leisure activities,
    entertainment, events, guest recreation and coordination
    with tourism, beach, transport and reception.
    """
    return {
        "module": "leisure",
        "status": "active",
        "message": "Leisure module is running",
    }