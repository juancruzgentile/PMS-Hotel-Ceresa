def test_guests_status(client):
    response = client.get("/guests/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "guests"
    assert data["status"] == "active"
    assert data["message"] == "Guests module is running"


def test_guests_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    guests_module = next(
        module for module in modules if module["name"] == "guests"
    )

    assert guests_module["enabled"] is True
    assert guests_module["implemented"] is True
    assert guests_module["loaded"] is True
    assert guests_module["error"] is None


def test_create_guest(client, reset_test_data):
    response = client.post(
        "/guests",
        json={
            "guest_code": "TEST-001",
            "first_name": "Mario",
            "last_name": "Rossi",
            "email": "test_mario@example.com",
            "phone": "+39 000000000",
            "nationality": "Italian",
            "notes": "Guest created by pytest.",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Guest created successfully"
    assert isinstance(response.json()["guest_id"], int)


def test_list_guests(client, reset_test_data):
    client.post(
        "/guests",
        json={
            "guest_code": "TEST-002",
            "first_name": "Laura",
            "last_name": "Bianchi",
            "email": None,
            "phone": None,
            "nationality": "Italian",
            "notes": None,
        },
    )

    response = client.get("/guests")

    assert response.status_code == 200

    guests = response.json()
    guest_codes = [guest["guest_code"] for guest in guests]

    assert "TEST-002" in guest_codes


def test_get_guest_by_id(client, reset_test_data):
    create_response = client.post(
        "/guests",
        json={
            "guest_code": "TEST-003",
            "first_name": "Ana",
            "last_name": "Garcia",
            "email": "test_ana@example.com",
            "phone": None,
            "nationality": "Spanish",
            "notes": None,
        },
    )

    guest_id = create_response.json()["guest_id"]

    response = client.get(f"/guests/{guest_id}")

    assert response.status_code == 200
    assert response.json()["guest_code"] == "TEST-003"
    assert response.json()["first_name"] == "Ana"


def test_duplicate_guest_code_is_rejected(client, reset_test_data):
    payload = {
        "guest_code": "TEST-004",
        "first_name": "First",
        "last_name": "Guest",
        "email": None,
        "phone": None,
        "nationality": None,
        "notes": None,
    }

    first_response = client.post("/guests", json=payload)
    second_response = client.post("/guests", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 409