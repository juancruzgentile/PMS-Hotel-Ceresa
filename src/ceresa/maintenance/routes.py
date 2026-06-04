from fastapi import APIRouter

from ceresa.rooms.repository import list_rooms_needing_repair


router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.get("/repair-rooms")
def get_repair_rooms() -> list[dict]:
    """
    Returns all rooms that need maintenance.

    This endpoint is designed for the maintenance sector.
    It only shows rooms where maintenance_status is 'needs_repair'.
    """
    return list_rooms_needing_repair()