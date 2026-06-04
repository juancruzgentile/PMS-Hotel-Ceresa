from fastapi import APIRouter

from ceresa.rooms.repository import list_dirty_rooms


router = APIRouter(prefix="/housekeeping", tags=["Housekeeping"])


@router.get("/dirty-rooms")
def get_dirty_rooms() -> list[dict]:
    """
    Returns all rooms that need cleaning.

    This endpoint is designed for the housekeeping sector.
    It only shows rooms where cleaning_status is 'dirty'.
    """
    return list_dirty_rooms()