def test_billing_status(client):
    response = client.get("/billing/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "billing"
    assert data["status"] == "active"
    assert data["message"] == "Billing module is running"


def test_billing_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    billing_module = next(
        module for module in modules if module["name"] == "billing"
    )

    assert billing_module["enabled"] is True
    assert billing_module["implemented"] is True
    assert billing_module["loaded"] is True
    assert billing_module["error"] is None

def create_reservation_for_billing(
    client,
    suffix: str,
) -> int:
    guest_response = client.post(
        "/guests",
        json={
            "guest_code": f"TEST-BILL-GUEST-{suffix}",
            "first_name": "Billing",
            "last_name": "Guest",
            "email": None,
            "phone": None,
            "nationality": None,
            "notes": None,
        },
    )

    assert guest_response.status_code == 200
    guest_id = guest_response.json()["guest_id"]

    room_response = client.post(
        "/rooms",
        json={
            "room_number": f"TEST-BILL-ROOM-{suffix}",
            "floor": 1,
            "room_type": "Billing Test",
            "has_jacuzzi": False,
            "has_balcony": False,
            "notes": None,
        },
    )

    assert room_response.status_code == 200
    room_id = room_response.json()["room_id"]

    reservation_response = client.post(
        "/reservations",
        json={
            "reservation_code": f"TEST-BILL-RES-{suffix}",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": "2027-12-01",
            "check_out_date": "2027-12-05",
            "status": "confirmed",
            "adults": 2,
            "children": 0,
            "notes": None,
        },
    )

    assert reservation_response.status_code == 200

    return reservation_response.json()["reservation_id"]


def test_create_billing_account(client, reset_test_data):
    reservation_id = create_reservation_for_billing(
        client,
        "001",
    )

    response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": "Billing account created by pytest.",
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "Billing account created successfully"
    )
    assert isinstance(
        response.json()["billing_account_id"],
        int,
    )


def test_duplicate_billing_account_is_rejected(
    client,
    reset_test_data,
):
    reservation_id = create_reservation_for_billing(
        client,
        "002",
    )

    payload = {
        "reservation_id": reservation_id,
        "notes": None,
    }

    first_response = client.post(
        "/billing/accounts",
        json=payload,
    )
    second_response = client.post(
        "/billing/accounts",
        json=payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_billing_account_calculates_balance(
    client,
    reset_test_data,
):
    reservation_id = create_reservation_for_billing(
        client,
        "003",
    )

    account_response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": None,
        },
    )

    account_id = account_response.json()[
        "billing_account_id"
    ]

    first_charge = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "rooms",
            "description": "Accommodation",
            "amount_cents": 12500,
        },
    )

    second_charge = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "bar",
            "description": "Bar consumption",
            "amount_cents": 2500,
        },
    )

    payment = client.post(
        f"/billing/accounts/{account_id}/payments",
        json={
            "payment_method": "card",
            "amount_cents": 10000,
            "reference": "TEST-PAYMENT-001",
        },
    )

    assert first_charge.status_code == 200
    assert second_charge.status_code == 200
    assert payment.status_code == 200

    response = client.get(
        f"/billing/accounts/{account_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["charges_total_cents"] == 15000
    assert data["payments_total_cents"] == 10000
    assert data["balance_cents"] == 5000
    assert data["currency"] == "EUR"
    assert len(data["charges"]) == 2
    assert len(data["payments"]) == 1


def test_billing_account_requires_valid_reservation(
    client,
    reset_test_data,
):
    response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": 999999,
            "notes": None,
        },
    )

    assert response.status_code == 404


def test_charge_requires_valid_account(
    client,
    reset_test_data,
):
    response = client.post(
        "/billing/accounts/999999/charges",
        json={
            "source_module": "bar",
            "description": "Invalid charge",
            "amount_cents": 1000,
        },
    )

    assert response.status_code == 404