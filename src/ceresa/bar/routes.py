from fastapi import APIRouter


router = APIRouter(prefix="/bar", tags=["Bar"])


@router.get("/status")
def get_bar_status() -> dict:
    """
    Returns the basic status of the bar module.

    This module will later manage bar operations,
    drinks, coffee service, guest orders, stock control
    and coordination with sala and reception.
    """
    return {
        "module": "bar",
        "status": "active",
        "message": "Bar module is running",
    }