from datetime import date
from importlib import import_module
from typing import Any

from ceresa.core import module_loader
from ceresa.core.settings import HOTEL_CONFIG
from ceresa.db import get_connection


class ReceptionDependencyUnavailable(RuntimeError):
    """
    Raised when an operational dependency cannot be used.
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        super().__init__(f"{module_name} module is unavailable.")


class ReceptionBusinessRuleError(RuntimeError):
    """
    Raised when a Reception operation violates a business rule.
    """


class ReceptionNotFoundError(RuntimeError):
    """
    Raised when a required Reception resource does not exist.
    """


def _ensure_module_available(module_name: str) -> None:
    if not module_loader.is_module_enabled(module_name):
        raise ReceptionDependencyUnavailable(module_name)

    if not module_loader.is_module_loaded(module_name):
        raise ReceptionDependencyUnavailable(module_name)


def _load_repository(module_name: str) -> Any:
    _ensure_module_available(module_name)

    try:
        return import_module(f"ceresa.{module_name}.repository")

    except Exception as error:
        raise ReceptionDependencyUnavailable(module_name) from error


def _call_dependency(
    module_name: str,
    operation: Any,
) -> Any:
    try:
        return operation()

    except (
        ReceptionBusinessRuleError,
        ReceptionDependencyUnavailable,
        ReceptionNotFoundError,
    ):
        raise

    except Exception as error:
        raise ReceptionDependencyUnavailable(module_name) from error


def _validate_room_ready_for_check_in(room: dict[str, Any]) -> None:
    if room["room_status"] != "available":
        raise ReceptionBusinessRuleError(
            "Room is not available for check-in."
        )

    if room["cleaning_status"] != "clean":
        raise ReceptionBusinessRuleError(
            "Room must be clean before check-in."
        )

    if room["maintenance_status"] != "ok":
        raise ReceptionBusinessRuleError(
            "Room must not require maintenance before check-in."
        )


def _get_billing_repository_if_enabled() -> Any | None:
    if not module_loader.is_module_enabled("billing"):
        return None

    return _load_repository("billing")


def check_in_reservation(reservation_id: int) -> dict[str, Any]:
    """
    Completes a reservation check-in in one SQLite transaction.
    """
    reservations_repository = _load_repository("reservations")
    rooms_repository = _load_repository("rooms")
    connection = get_connection()

    try:
        connection.execute("BEGIN")

        reservation = _call_dependency(
            "reservations",
            lambda: reservations_repository.get_reservation_by_id_with_connection(
                connection,
                reservation_id,
            ),
        )
        if reservation is None:
            raise ReceptionNotFoundError("Reservation not found.")

        if reservation["status"] != "confirmed":
            raise ReceptionBusinessRuleError(
                "Only confirmed reservations can be checked in."
            )

        room = _call_dependency(
            "rooms",
            lambda: rooms_repository.get_room_by_id_with_connection(
                connection,
                reservation["room_id"],
            ),
        )
        if room is None:
            raise ReceptionNotFoundError("Room not found.")

        _validate_room_ready_for_check_in(room)

        billing_repository = _get_billing_repository_if_enabled()
        billing_enabled = billing_repository is not None
        billing_account_id = None

        if billing_enabled:
            billing_account = _call_dependency(
                "billing",
                lambda: billing_repository.get_billing_account_by_reservation_id_with_connection(
                    connection,
                    reservation_id,
                ),
            )

            if billing_account is None:
                billing_account_id = _call_dependency(
                    "billing",
                    lambda: billing_repository.create_billing_account_with_connection(
                        connection,
                        reservation_id,
                        None,
                    ),
                )
            else:
                if billing_account["status"] != "open":
                    raise ReceptionBusinessRuleError(
                        "Billing account must be open before check-in."
                    )

                billing_account_id = billing_account["id"]

        _call_dependency(
            "reservations",
            lambda: reservations_repository.update_reservation_status_with_connection(
                connection,
                reservation_id,
                "checked_in",
            ),
        )
        _call_dependency(
            "rooms",
            lambda: rooms_repository.update_room_operational_status_with_connection(
                connection,
                room["id"],
                "occupied",
            ),
        )

        connection.commit()

        return {
            "message": "Check-in completed successfully",
            "reservation_id": reservation_id,
            "room_id": room["id"],
            "reservation_status": "checked_in",
            "room_status": "occupied",
            "billing_enabled": billing_enabled,
            "billing_account_id": billing_account_id,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def check_out_reservation(reservation_id: int) -> dict[str, Any]:
    """
    Completes a reservation check-out in one SQLite transaction.
    """
    reservations_repository = _load_repository("reservations")
    rooms_repository = _load_repository("rooms")
    connection = get_connection()

    try:
        connection.execute("BEGIN")

        reservation = _call_dependency(
            "reservations",
            lambda: reservations_repository.get_reservation_by_id_with_connection(
                connection,
                reservation_id,
            ),
        )
        if reservation is None:
            raise ReceptionNotFoundError("Reservation not found.")

        if reservation["status"] != "checked_in":
            raise ReceptionBusinessRuleError(
                "Only checked-in reservations can be checked out."
            )

        room = _call_dependency(
            "rooms",
            lambda: rooms_repository.get_room_by_id_with_connection(
                connection,
                reservation["room_id"],
            ),
        )
        if room is None:
            raise ReceptionNotFoundError("Room not found.")

        if room["room_status"] != "occupied":
            raise ReceptionBusinessRuleError(
                "Room must be occupied before check-out."
            )

        billing_repository = _get_billing_repository_if_enabled()
        billing_enabled = billing_repository is not None
        billing_account = None
        billing_account_status = None

        if billing_enabled:
            billing_account = _call_dependency(
                "billing",
                lambda: billing_repository.get_billing_account_by_reservation_id_with_connection(
                    connection,
                    reservation_id,
                ),
            )

            if billing_account is None:
                raise ReceptionBusinessRuleError(
                    "Billing account is required before check-out."
                )

            if billing_account["status"] != "open":
                raise ReceptionBusinessRuleError(
                    "Billing account must be open before check-out."
                )

            if billing_account["balance_cents"] != 0:
                raise ReceptionBusinessRuleError(
                    "Billing account balance must be zero before check-out."
                )

            billing_account_status = "closed"

        final_room_status = (
            "available"
            if room["maintenance_status"] == "ok"
            else "out_of_service"
        )

        _call_dependency(
            "reservations",
            lambda: reservations_repository.update_reservation_status_with_connection(
                connection,
                reservation_id,
                "checked_out",
            ),
        )
        _call_dependency(
            "rooms",
            lambda: rooms_repository.update_room_operational_status_with_connection(
                connection,
                room["id"],
                final_room_status,
                "dirty",
            ),
        )

        if billing_enabled:
            _call_dependency(
                "billing",
                lambda: billing_repository.close_billing_account_with_connection(
                    connection,
                    billing_account["id"],
                ),
            )

        connection.commit()

        return {
            "message": "Check-out completed successfully",
            "reservation_id": reservation_id,
            "room_id": room["id"],
            "reservation_status": "checked_out",
            "room_status": final_room_status,
            "cleaning_status": "dirty",
            "billing_enabled": billing_enabled,
            "billing_account_status": billing_account_status,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def list_arrivals(arrival_date: date) -> list[dict[str, Any]]:
    """
    Returns non-cancelled reservations arriving on the given date.
    """
    reservations_repository = _load_repository("reservations")

    try:
        return reservations_repository.list_reservations_by_check_in_date(
            arrival_date.isoformat()
        )

    except Exception as error:
        raise ReceptionDependencyUnavailable("reservations") from error


def list_departures(departure_date: date) -> list[dict[str, Any]]:
    """
    Returns non-cancelled reservations departing on the given date.
    """
    reservations_repository = _load_repository("reservations")

    try:
        return reservations_repository.list_reservations_by_check_out_date(
            departure_date.isoformat()
        )

    except Exception as error:
        raise ReceptionDependencyUnavailable("reservations") from error


def get_reservation_summary(reservation_id: int) -> dict[str, Any] | None:
    """
    Returns reservation details and optional billing account information.
    """
    reservations_repository = _load_repository("reservations")

    try:
        reservation = reservations_repository.get_reservation_by_id(
            reservation_id
        )

    except Exception as error:
        raise ReceptionDependencyUnavailable("reservations") from error

    if reservation is None:
        return None

    if not module_loader.is_module_enabled("billing"):
        return {
            "reservation": reservation,
            "billing_enabled": False,
            "billing_account": None,
        }

    billing_repository = _load_repository("billing")

    try:
        billing_account = (
            billing_repository.get_billing_account_by_reservation_id(
                reservation_id
            )
        )

    except Exception as error:
        raise ReceptionDependencyUnavailable("billing") from error

    if billing_account is not None:
        billing_account["currency"] = HOTEL_CONFIG["currency"]

    return {
        "reservation": reservation,
        "billing_enabled": True,
        "billing_account": billing_account,
    }
