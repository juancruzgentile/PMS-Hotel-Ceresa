from datetime import date
import json
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ceresa.audit import repository as audit_repository
from ceresa.db import get_connection
from ceresa.reservations import repository
from ceresa.users import repository as users_repository


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


class ReservationCancelRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=500,
    )
    actor_user_id: int | None = Field(default=None, ge=1)


class ReservationDatesUpdate(BaseModel):
    check_in_date: date
    check_out_date: date
    actor_user_id: int | None = Field(default=None, ge=1)


class ReservationRoomUpdate(BaseModel):
    room_id: int = Field(..., ge=1)
    actor_user_id: int | None = Field(default=None, ge=1)


def _serialize_state(state: dict) -> str:
    return json.dumps(state, sort_keys=True)


def _build_reservation_state(reservation: dict) -> dict:
    return {
        "reservation_status": reservation["status"],
        "room_id": reservation["room_id"],
        "check_in_date": reservation["check_in_date"],
        "check_out_date": reservation["check_out_date"],
    }


def _validate_actor_user_if_present(
    connection,
    actor_user_id: int | None,
) -> None:
    if actor_user_id is None:
        return

    user = users_repository.get_user_by_id_with_connection(
        connection,
        actor_user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Actor user not found.",
        )


def _create_reservation_audit_event(
    connection,
    event_type: str,
    reservation_id: int,
    room_id: int,
    actor_user_id: int | None,
    before_state: dict,
    after_state: dict,
    metadata: dict | None = None,
) -> None:
    audit_repository.create_audit_event_with_connection(
        connection,
        {
            "module": "reservations",
            "event_type": event_type,
            "entity_type": "reservation",
            "entity_id": reservation_id,
            "reservation_id": reservation_id,
            "room_id": room_id,
            "billing_account_id": None,
            "actor_user_id": actor_user_id,
            "before_state_json": _serialize_state(before_state),
            "after_state_json": _serialize_state(after_state),
            "metadata_json": _serialize_state(metadata or {}),
        },
    )


def _require_editable_reservation(reservation: dict) -> None:
    if reservation["status"] in {"cancelled", "checked_out"}:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cancelled or checked-out reservations cannot be "
                "changed."
            ),
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


@router.patch("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    payload: ReservationCancelRequest,
) -> dict:
    """
    Cancels a pending or confirmed reservation.
    """
    reason = payload.reason.strip() if payload.reason else None
    connection = get_connection()

    try:
        connection.execute("BEGIN")
        _validate_actor_user_if_present(
            connection,
            payload.actor_user_id,
        )

        reservation = repository.get_reservation_by_id_with_connection(
            connection,
            reservation_id,
        )
        if reservation is None:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found.",
            )

        if reservation["status"] == "cancelled":
            raise HTTPException(
                status_code=409,
                detail="Reservation is already cancelled.",
            )

        if reservation["status"] not in {"pending", "confirmed"}:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Only pending or confirmed reservations can be "
                    "cancelled."
                ),
            )

        before_state = _build_reservation_state(reservation)
        repository.update_reservation_status_with_connection(
            connection,
            reservation_id,
            "cancelled",
        )
        after_state = dict(before_state)
        after_state["reservation_status"] = "cancelled"

        _create_reservation_audit_event(
            connection,
            "reservation_cancelled",
            reservation_id,
            reservation["room_id"],
            payload.actor_user_id,
            before_state,
            after_state,
            {"reason": reason} if reason else {},
        )

        connection.commit()

        return {
            "message": "Reservation cancelled successfully",
            "reservation_id": reservation_id,
            "status": "cancelled",
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


@router.patch("/{reservation_id}/dates")
def update_reservation_dates(
    reservation_id: int,
    payload: ReservationDatesUpdate,
) -> dict:
    """
    Updates reservation dates after overlap validation.
    """
    if payload.check_out_date <= payload.check_in_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date.",
        )

    check_in_date = payload.check_in_date.isoformat()
    check_out_date = payload.check_out_date.isoformat()
    connection = get_connection()

    try:
        connection.execute("BEGIN")
        _validate_actor_user_if_present(
            connection,
            payload.actor_user_id,
        )

        reservation = repository.get_reservation_by_id_with_connection(
            connection,
            reservation_id,
        )
        if reservation is None:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found.",
            )

        _require_editable_reservation(reservation)

        if repository.room_has_overlapping_reservation_with_connection(
            connection=connection,
            room_id=reservation["room_id"],
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            exclude_reservation_id=reservation_id,
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "The room already has an overlapping reservation."
                ),
            )

        before_state = _build_reservation_state(reservation)
        repository.update_reservation_dates_with_connection(
            connection,
            reservation_id,
            check_in_date,
            check_out_date,
        )
        after_state = dict(before_state)
        after_state["check_in_date"] = check_in_date
        after_state["check_out_date"] = check_out_date

        _create_reservation_audit_event(
            connection,
            "reservation_dates_changed",
            reservation_id,
            reservation["room_id"],
            payload.actor_user_id,
            before_state,
            after_state,
        )

        connection.commit()

        return {
            "message": "Reservation dates updated successfully",
            "reservation_id": reservation_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


@router.patch("/{reservation_id}/room")
def update_reservation_room(
    reservation_id: int,
    payload: ReservationRoomUpdate,
) -> dict:
    """
    Updates reservation room after existence and overlap validation.
    """
    connection = get_connection()

    try:
        connection.execute("BEGIN")
        _validate_actor_user_if_present(
            connection,
            payload.actor_user_id,
        )

        reservation = repository.get_reservation_by_id_with_connection(
            connection,
            reservation_id,
        )
        if reservation is None:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found.",
            )

        _require_editable_reservation(reservation)

        if not repository.room_exists_with_connection(
            connection,
            payload.room_id,
        ):
            raise HTTPException(
                status_code=404,
                detail="Room not found.",
            )

        if repository.room_has_overlapping_reservation_with_connection(
            connection=connection,
            room_id=payload.room_id,
            check_in_date=reservation["check_in_date"],
            check_out_date=reservation["check_out_date"],
            exclude_reservation_id=reservation_id,
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "The room already has an overlapping reservation."
                ),
            )

        before_state = _build_reservation_state(reservation)
        repository.update_reservation_room_with_connection(
            connection,
            reservation_id,
            payload.room_id,
        )
        after_state = dict(before_state)
        after_state["room_id"] = payload.room_id

        _create_reservation_audit_event(
            connection,
            "reservation_room_changed",
            reservation_id,
            payload.room_id,
            payload.actor_user_id,
            before_state,
            after_state,
            {"previous_room_id": reservation["room_id"]},
        )

        connection.commit()

        return {
            "message": "Reservation room updated successfully",
            "reservation_id": reservation_id,
            "room_id": payload.room_id,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
