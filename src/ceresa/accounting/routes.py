from fastapi import APIRouter


router = APIRouter(prefix="/accounting", tags=["Accounting"])


@router.get("/status")
def get_accounting_status() -> dict:
    """
    Returns the basic status of the accounting module.

    This module will later manage hotel income,
    expenses, suppliers, payroll, taxes,
    financial reports and accounting operations.
    """
    return {
        "module": "accounting",
        "status": "active",
        "message": "Accounting module is running",
    }