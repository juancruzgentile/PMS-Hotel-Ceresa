from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ceresa.rooms import repository


router = APIRouter(prefix="/rooms", tags=["Rooms"])


class RoomCreate(BaseModel):
    room_number: str = Field(..., min_length=1, max_length=20)
    floor: int = Field(..., ge=0)
    room_type: str = Field(..., min_length=2, max_length=50)
    has_jacuzzi: bool = False
    has_balcony: bool = False
    notes: str | None = None


class RoomUpdateStatus(BaseModel):
    room_status: str | None = None
    cleaning_status: str | None = None
    maintenance_status: str | None = None


@router.post("")
def create_room(room: RoomCreate) -> dict:
    """
    Creates a hotel room.
    """
    try:
        room_id = repository.create_room(room.model_dump())

        return {
            "message": "Room created successfully",
            "room_id": room_id,
        }

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(
                status_code=409,
                detail="A room with this number already exists.",
            )

        raise HTTPException(status_code=500, detail=str(error))


@router.get("")
def list_rooms() -> list[dict]:
    """
    Returns all hotel rooms.
    """
    return repository.list_rooms()


@router.get("/{room_id}")
def get_room(room_id: int) -> dict:
    """
    Returns one room by ID.
    """
    room = repository.get_room_by_id(room_id)

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found.")

    return room


@router.patch("/{room_id}/status")
def update_room_status(room_id: int, status: RoomUpdateStatus) -> dict:
    """
    Updates operational, cleaning or maintenance status of a room.
    """
    allowed_room_status = {"available", "occupied", "out_of_service"}
    allowed_cleaning_status = {"clean", "dirty", "in_progress"}
    allowed_maintenance_status = {"ok", "needs_repair", "in_repair"}

    if status.room_status is not None and status.room_status not in allowed_room_status:
        raise HTTPException(status_code=400, detail="Invalid room_status.")

    if status.cleaning_status is not None and status.cleaning_status not in allowed_cleaning_status:
        raise HTTPException(status_code=400, detail="Invalid cleaning_status.")

    if (
        status.maintenance_status is not None
        and status.maintenance_status not in allowed_maintenance_status
    ):
        raise HTTPException(status_code=400, detail="Invalid maintenance_status.")

    was_updated = repository.update_room_status(
        room_id=room_id,
        room_status=status.room_status,
        cleaning_status=status.cleaning_status,
        maintenance_status=status.maintenance_status,
    )

    if not was_updated:
        raise HTTPException(status_code=404, detail="Room not found.")

    return {
        "message": "Room status updated successfully",
        "room_id": room_id,
    }


@router.delete("/{room_id}")
def delete_room(room_id: int) -> dict:
    """
    Deletes a room.

    Later we may replace this with soft delete,
    because in real hotels deleting historical data is dangerous.
    """
    was_deleted = repository.delete_room(room_id)

    if not was_deleted:
        raise HTTPException(status_code=404, detail="Room not found.")

    return {
        "message": "Room deleted successfully",
        "room_id": room_id,
    }