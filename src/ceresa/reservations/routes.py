from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ceresa.reservations import repository


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
)


class ReservationCreate(BaseModel):
    reservation_code: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    guest_id: int = Field(..., ge=1)
    room_id: int = Field(..., ge=1)

    check_in_date: date
    check_out_date: date

    status: Literal[
        "pending",
        "confirmed",
    ] = "pending"

    adults: int = Field(default=1, ge=1, le=20)
    children: int = Field(default=0, ge=0, le=20)

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


@router.get("/status")
def get_reservations_status() -> dict:
    """
    Returns the basic module status.
    """
    return {
        "module": "reservations",
        "status": "active",
        "message": "Reservations module is running",
    }


@router.post("")
def create_reservation(
    reservation: ReservationCreate,
) -> dict:
    """
    Creates a hotel reservation.
    """
    if reservation.check_out_date <= reservation.check_in_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date.",
        )

    if not repository.guest_exists(reservation.guest_id):
        raise HTTPException(
            status_code=404,
            detail="Guest not found or inactive.",
        )

    if not repository.room_exists(reservation.room_id):
        raise HTTPException(
            status_code=404,
            detail="Room not found.",
        )

    reservation_data = reservation.model_dump(mode="json")
    reservation_data["reservation_code"] = (
        reservation_data["reservation_code"]
        .strip()
        .upper()
    )

    if repository.room_has_overlapping_reservation(
        room_id=reservation.room_id,
        check_in_date=reservation_data["check_in_date"],
        check_out_date=reservation_data["check_out_date"],
    ):
        raise HTTPException(
            status_code=409,
            detail="The room already has an overlapping reservation.",
        )

    try:
        reservation_id = repository.create_reservation(
            reservation_data
        )

    except Exception as error:
        if repository.is_unique_constraint_error(error):
            raise HTTPException(
                status_code=409,
                detail="A reservation with this code already exists.",
            )

        raise

    return {
        "message": "Reservation created successfully",
        "reservation_id": reservation_id,
    }


@router.get("")
def list_reservations() -> list[dict]:
    """
    Returns all hotel reservations.
    """
    return repository.list_reservations()


@router.get("/{reservation_id}")
def get_reservation(reservation_id: int) -> dict:
    """
    Returns one hotel reservation.
    """
    reservation = repository.get_reservation_by_id(
        reservation_id
    )

    if reservation is None:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found.",
        )

    return reservation