from datetime import date

from fastapi import APIRouter, HTTPException, status

from ceresa.reception import service


router = APIRouter(prefix="/reception", tags=["Reception"])


def _raise_http_error(error: Exception) -> None:
    if isinstance(error, service.ReceptionNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    if isinstance(error, service.ReceptionBusinessRuleError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    if isinstance(error, service.ReceptionDependencyUnavailable):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{error.module_name} module is unavailable.",
        )

    raise error


@router.get("/status")
def get_reception_status() -> dict:
    """
    Returns the basic status of the reception module.

    This module will later manage check-in, check-out,
    guest requests, room assignment and coordination
    with other hotel sectors.
    """
    return {
        "module": "reception",
        "status": "active",
        "message": "Reception module is running",
    }


@router.get("/arrivals")
def list_arrivals(arrival_date: date) -> list[dict]:
    """
    Returns reservations arriving on the requested date.
    """
    try:
        return service.list_arrivals(arrival_date)

    except service.ReceptionDependencyUnavailable as error:
        _raise_http_error(error)


@router.get("/departures")
def list_departures(departure_date: date) -> list[dict]:
    """
    Returns reservations departing on the requested date.
    """
    try:
        return service.list_departures(departure_date)

    except service.ReceptionDependencyUnavailable as error:
        _raise_http_error(error)


@router.get("/reservations/{reservation_id}/summary")
def get_reservation_summary(reservation_id: int) -> dict:
    """
    Returns an operational reservation summary for Reception.
    """
    try:
        summary = service.get_reservation_summary(reservation_id)

    except service.ReceptionDependencyUnavailable as error:
        _raise_http_error(error)

    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        )

    return summary


@router.post("/reservations/{reservation_id}/check-in")
def check_in_reservation(reservation_id: int) -> dict:
    """
    Completes a reservation check-in.
    """
    try:
        return service.check_in_reservation(reservation_id)

    except (
        service.ReceptionBusinessRuleError,
        service.ReceptionDependencyUnavailable,
        service.ReceptionNotFoundError,
    ) as error:
        _raise_http_error(error)


@router.post("/reservations/{reservation_id}/check-out")
def check_out_reservation(reservation_id: int) -> dict:
    """
    Completes a reservation check-out.
    """
    try:
        return service.check_out_reservation(reservation_id)

    except (
        service.ReceptionBusinessRuleError,
        service.ReceptionDependencyUnavailable,
        service.ReceptionNotFoundError,
    ) as error:
        _raise_http_error(error)
