import json
from typing import Any

from fastapi import APIRouter, Query

from ceresa.audit import repository


router = APIRouter(prefix="/audit", tags=["Audit"])


def _parse_event_json(raw_value: str | None) -> dict[str, Any]:
    if raw_value is None:
        return {}

    return json.loads(raw_value)


def _present_audit_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": event["id"],
        "module": event["module"],
        "event_type": event["event_type"],
        "entity_type": event["entity_type"],
        "entity_id": event["entity_id"],
        "reservation_id": event["reservation_id"],
        "room_id": event["room_id"],
        "billing_account_id": event["billing_account_id"],
        "actor_user_id": event["actor_user_id"],
        "before_state": _parse_event_json(event["before_state_json"]),
        "after_state": _parse_event_json(event["after_state_json"]),
        "metadata": _parse_event_json(event["metadata_json"]),
        "created_at": event["created_at"],
    }


@router.get("/events")
def list_audit_events(
    reservation_id: int | None = Query(default=None, ge=1),
    room_id: int | None = Query(default=None, ge=1),
    billing_account_id: int | None = Query(default=None, ge=1),
    actor_user_id: int | None = Query(default=None, ge=1),
    module: str | None = Query(default=None, min_length=1, max_length=50),
    event_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    """
    Returns immutable audit events with optional filters.
    """
    events = repository.list_audit_events(
        reservation_id=reservation_id,
        room_id=room_id,
        billing_account_id=billing_account_id,
        actor_user_id=actor_user_id,
        module=module,
        event_type=event_type,
        limit=limit,
    )

    return [_present_audit_event(event) for event in events]
