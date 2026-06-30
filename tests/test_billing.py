from ceresa.db import get_connection


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

    assert response.status_code == 201
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

    assert first_response.status_code == 201
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

    assert first_charge.status_code == 201
    assert second_charge.status_code == 201
    assert payment.status_code == 201

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


def test_list_billing_accounts_includes_created_account_and_balance(
    client,
    reset_test_data,
):
    reservation_id = create_reservation_for_billing(
        client,
        "L01",
    )
    account_response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": None,
        },
    )
    account_id = account_response.json()["billing_account_id"]

    charge_response = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "rooms",
            "description": "Accommodation",
            "amount_cents": 12000,
        },
    )
    payment_response = client.post(
        f"/billing/accounts/{account_id}/payments",
        json={
            "payment_method": "cash",
            "amount_cents": 5000,
            "reference": None,
        },
    )

    assert account_response.status_code == 201
    assert charge_response.status_code == 201
    assert payment_response.status_code == 201

    response = client.get("/billing/accounts")

    assert response.status_code == 200

    accounts = response.json()
    account = next(
        item
        for item in accounts
        if item["billing_account_id"] == account_id
    )

    assert account["reservation_id"] == reservation_id
    assert account["reservation_code"] == "TEST-BILL-RES-L01"
    assert account["guest_name"] == "Billing Guest"
    assert account["room_number"] == "TEST-BILL-ROOM-L01"
    assert account["currency"] == "EUR"
    assert account["total_charges_cents"] == 12000
    assert account["total_payments_cents"] == 5000
    assert account["balance_cents"] == 7000


def test_get_billing_account_by_reservation_returns_existing_account(
    client,
    reset_test_data,
):
    reservation_id = create_reservation_for_billing(
        client,
        "RA1",
    )
    account_response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": None,
        },
    )
    account_id = account_response.json()["billing_account_id"]

    charge_response = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "rooms",
            "description": "Accommodation",
            "amount_cents": 15000,
        },
    )

    assert account_response.status_code == 201
    assert charge_response.status_code == 201

    response = client.get(
        f"/billing/reservations/{reservation_id}/account"
    )

    assert response.status_code == 200

    account = response.json()

    assert account["id"] == account_id
    assert account["reservation_id"] == reservation_id
    assert account["charges_total_cents"] == 15000
    assert account["payments_total_cents"] == 0
    assert account["balance_cents"] == 15000
    assert account["currency"] == "EUR"
    assert len(account["charges"]) == 1
    assert account["payments"] == []


def test_get_billing_account_by_reservation_returns_404_without_account(
    client,
    reset_test_data,
):
    reservation_id = create_reservation_for_billing(
        client,
        "RA4",
    )

    response = client.get(
        f"/billing/reservations/{reservation_id}/account"
    )

    assert response.status_code == 404


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


def test_payment_requires_valid_account(
    client,
    reset_test_data,
):
    response = client.post(
        "/billing/accounts/999999/payments",
        json={
            "payment_method": "card",
            "amount_cents": 1000,
            "reference": "INVALID-PAYMENT",
        },
    )

    assert response.status_code == 404


def test_billing_inputs_are_normalized(
    client,
    reset_test_data,
):
    reservation_id = create_reservation_for_billing(
        client,
        "004",
    )
    account_response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": None,
        },
    )
    account_id = account_response.json()["billing_account_id"]

    charge_response = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "  BAR  ",
            "description": "  Pool drinks  ",
            "amount_cents": 1800,
        },
    )
    payment_response = client.post(
        f"/billing/accounts/{account_id}/payments",
        json={
            "payment_method": "  CARD  ",
            "amount_cents": 1800,
            "reference": "  CARD-004  ",
        },
    )

    assert charge_response.status_code == 201
    assert payment_response.status_code == 201

    response = client.get(f"/billing/accounts/{account_id}")
    data = response.json()

    assert data["charges"][0]["source_module"] == "bar"
    assert data["charges"][0]["description"] == "Pool drinks"
    assert data["payments"][0]["payment_method"] == "card"
    assert data["payments"][0]["reference"] == "CARD-004"


def test_payment_method_must_be_supported(
    client,
    reset_test_data,
):
    reservation_id = create_reservation_for_billing(
        client,
        "005",
    )
    account_response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": None,
        },
    )
    account_id = account_response.json()["billing_account_id"]

    response = client.post(
        f"/billing/accounts/{account_id}/payments",
        json={
            "payment_method": "crypto",
            "amount_cents": 2500,
            "reference": None,
        },
    )

    assert response.status_code == 422


def test_closed_billing_account_rejects_movements(
    client,
    reset_test_data,
):
    reservation_id = create_reservation_for_billing(
        client,
        "006",
    )
    account_response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": None,
        },
    )
    account_id = account_response.json()["billing_account_id"]

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE billing_accounts
            SET status = 'closed'
            WHERE id = ?
            """,
            (account_id,),
        )
        connection.commit()

    charge_response = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "bar",
            "description": "Late minibar charge",
            "amount_cents": 900,
        },
    )
    payment_response = client.post(
        f"/billing/accounts/{account_id}/payments",
        json={
            "payment_method": "cash",
            "amount_cents": 900,
            "reference": None,
        },
    )

    assert charge_response.status_code == 409
    assert payment_response.status_code == 409
