from fastapi import APIRouter


router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/status")
def get_inventory_status() -> dict:
    """
    Returns the basic status of the inventory module.

    This module will later manage shared stock,
    sector-specific inventories, movements, minimum quantities,
    suppliers and coordination with hotel departments.
    """
    return {
        "module": "inventory",
        "status": "active",
        "message": "Inventory module is running",
    }