from fastapi import APIRouter


router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/status")
def get_billing_status() -> dict:
    """
    Returns the basic status of the billing module.

    This module will later manage guest bills,
    payments, room charges, extra services,
    check-out balances and coordination with
    reservations and reception.
    """
    return {
        "module": "billing",
        "status": "active",
        "message": "Billing module is running",
    }