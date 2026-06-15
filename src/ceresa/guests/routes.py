from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ceresa.guests import repository


router = APIRouter(prefix="/guests", tags=["Guests"])


class GuestCreate(BaseModel):
    guest_code: str = Field(..., min_length=2, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

    email: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=50)
    nationality: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)


@router.get("/status")
def get_guests_status() -> dict:
    """
    Returns the basic module status.
    """
    return {
        "module": "guests",
        "status": "active",
        "message": "Guests module is running",
    }


@router.post("")
def create_guest(guest: GuestCreate) -> dict:
    """
    Creates a hotel guest profile.
    """
    guest_data = guest.model_dump()

    guest_data["guest_code"] = guest_data["guest_code"].strip().upper()
    guest_data["first_name"] = guest_data["first_name"].strip()
    guest_data["last_name"] = guest_data["last_name"].strip()

    try:
        guest_id = repository.create_guest(guest_data)

    except Exception as error:
        if repository.is_unique_constraint_error(error):
            raise HTTPException(
                status_code=409,
                detail="A guest with this code already exists.",
            )

        raise

    return {
        "message": "Guest created successfully",
        "guest_id": guest_id,
    }


@router.get("")
def list_guests() -> list[dict]:
    """
    Returns all hotel guest profiles.
    """
    return repository.list_guests()


@router.get("/{guest_id}")
def get_guest(guest_id: int) -> dict:
    """
    Returns one hotel guest profile.
    """
    guest = repository.get_guest_by_id(guest_id)

    if guest is None:
        raise HTTPException(
            status_code=404,
            detail="Guest not found.",
        )

    return guest