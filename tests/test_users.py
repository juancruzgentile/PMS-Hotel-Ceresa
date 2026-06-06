def test_create_department(client, reset_test_data):
    response = client.post(
        "/users/departments",
        json={
            "code": "test_housekeeping",
            "name": "Test Housekeeping",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Department created successfully"
    assert isinstance(response.json()["department_id"], int)


def test_create_employee_requires_department(client, reset_test_data):
    response = client.post(
        "/users",
        json={
            "username": "test_employee_without_department",
            "full_name": "Test Employee",
            "email": None,
            "user_type": "employee",
            "department_id": None,
        },
    )

    assert response.status_code == 400


def test_create_employee_with_department(client, reset_test_data):
    department_response = client.post(
        "/users/departments",
        json={
            "code": "test_maintenance",
            "name": "Test Maintenance",
        },
    )
    department_id = department_response.json()["department_id"]

    user_response = client.post(
        "/users",
        json={
            "username": "test_maintenance_employee",
            "full_name": "Maintenance Employee",
            "email": "maintenance.test@example.com",
            "user_type": "employee",
            "department_id": department_id,
        },
    )

    assert user_response.status_code == 200
    assert user_response.json()["message"] == "User created successfully"


def test_create_supervisor_with_department(client, reset_test_data):
    department_response = client.post(
        "/users/departments",
        json={
            "code": "test_sala",
            "name": "Test Sala",
        },
    )
    department_id = department_response.json()["department_id"]

    user_response = client.post(
        "/users",
        json={
            "username": "test_sala_supervisor",
            "full_name": "Sala Supervisor",
            "email": "sala.supervisor@example.com",
            "user_type": "supervisor",
            "department_id": department_id,
        },
    )

    assert user_response.status_code == 200


def test_create_director_without_department(client, reset_test_data):
    response = client.post(
        "/users",
        json={
            "username": "test_director",
            "full_name": "Test Director",
            "email": "director.test@example.com",
            "user_type": "director",
            "department_id": None,
        },
    )

    assert response.status_code == 200


def test_director_cannot_have_department(client, reset_test_data):
    department_response = client.post(
        "/users/departments",
        json={
            "code": "test_accounting",
            "name": "Test Accounting",
        },
    )
    department_id = department_response.json()["department_id"]

    response = client.post(
        "/users",
        json={
            "username": "test_invalid_director",
            "full_name": "Invalid Director",
            "email": None,
            "user_type": "director",
            "department_id": department_id,
        },
    )

    assert response.status_code == 400