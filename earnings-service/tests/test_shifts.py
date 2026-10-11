
def test_create_shift_success(client):
    payload = {
        "platform": "Foodpanda",
        "date": "2026-10-11",
        "hours_worked": 6.5,
        "gross_earned": 4000.0,
        "deductions": 600.0,
        "net_received": 3400.0,
    }

    response = client.post("/shifts", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["platform"] == "Foodpanda"
    assert data["worker_id"] == "11111111-2222-3333-4444-555555555555"


def test_create_shift_net_exceeds_gross(client):
    payload = {
        "platform": "Uber",
        "date": "2026-10-12",
        "hours_worked": 8.0,
        "gross_earned": 5000.0,
        "deductions": 200.0,
        "net_received": 6000.0,
    }

    response = client.post("/shifts", json=payload)

    assert response.status_code == 400
    assert (
        "Net received cannot exceed gross earned"
        in response.json()["detail"]
    )


def test_list_shifts_authenticated(client):
    response = client.get("/shifts")

    assert response.status_code == 200
    data = response.json()
    assert "shifts" in data
    assert "count" in data


def test_get_shift_not_found(client):
    response = client.get(
        "/shifts/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404


def test_update_shift_not_found(client):
    payload = {"platform": "Updated Platform"}

    response = client.put(
        "/shifts/00000000-0000-0000-0000-000000000000",
        json=payload,
    )

    assert response.status_code == 404


def test_delete_shift_not_found(client):
    response = client.delete(
        "/shifts/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404


def test_earnings_summary(client):
    response = client.get("/earnings/summary")

    assert response.status_code == 200
    data = response.json()

    assert "total_hours" in data
    assert "total_gross" in data
    assert "total_deductions" in data
    assert "total_net" in data
    assert "total_shifts" in data
    assert "effective_hourly_rate" in data


def test_csv_import_is_explicitly_non_persisting(client):
    response = client.post(
        "/shifts/import-csv",
        json={
            "platform": "Foodpanda",
            "csv_text": "date,net_received\n2026-10-11,3400",
        },
    )

    assert response.status_code == 202
    assert response.json()["stub"] is True
    assert response.json()["rows_detected"] == 1


# -----------------------------------------
# UPDATE VALIDATION TESTS
# -----------------------------------------

EXISTING_SHIFT_ID = (
    "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
)


def test_update_shift_valid_partial(client):
    payload = {
        "platform": "Updated Platform"
    }

    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["platform"] == "Foodpanda"


def test_update_net_exceeds_existing_gross(client):
    payload = {
        "net_received": 5000.0
    }

    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json=payload,
    )

    assert response.status_code == 400
    assert (
        "Net received cannot exceed gross earned"
        in response.json()["detail"]
    )


def test_update_gross_below_existing_net(client):
    payload = {
        "gross_earned": 3000.0
    }

    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json=payload,
    )

    assert response.status_code == 400
    assert (
        "Net received cannot exceed gross earned"
        in response.json()["detail"]
    )


def test_update_negative_deductions(client):
    payload = {
        "deductions": -100.0
    }

    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json=payload,
    )

    assert response.status_code == 422


def test_update_zero_hours(client):
    payload = {
        "hours_worked": 0
    }

    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json=payload,
    )

    assert response.status_code == 422


def test_update_negative_hours(client):
    payload = {
        "hours_worked": -5
    }

    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json=payload,
    )

    assert response.status_code == 422


def test_update_negative_net_received(client):
    payload = {
        "net_received": -100
    }

    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json=payload,
    )

    assert response.status_code == 422


def test_update_negative_gross_earned(client):
    payload = {
        "gross_earned": -100
    }

    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json=payload,
    )

    assert response.status_code == 422


def test_update_empty_payload(client):
    response = client.put(
        f"/shifts/{EXISTING_SHIFT_ID}",
        json={},
    )

    assert response.status_code == 200
