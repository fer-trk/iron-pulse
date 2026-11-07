import pytest
from fastapi.testclient import TestClient

SHIFT_DATA = {
    "class_name": "Yoga",
    "instructor": "Carlos",
    "day_of_week": "monday",
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "max_capacity": 10,
    "active_slot": True
}

RESERVATION_DATA = {
    "shift_id": 1,
    "date": "2026-06-02"
}


def create_shift(client: TestClient, auth_headers, data=None):
    client.post("/api/v1/shifts/", json=data or SHIFT_DATA, headers=auth_headers)


def test_create_reservation(client: TestClient, auth_headers, active_member):
    create_shift(client, auth_headers)
    r = client.post("/api/v1/reservations/", json=RESERVATION_DATA, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["shift_id"] == 1
    assert data["status"] == "confirmed"
    assert data["id"] is not None


def test_create_reservation_shift_not_found(client: TestClient, auth_headers):
    r = client.post("/api/v1/reservations/", json=RESERVATION_DATA, headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["detail"] == "Shift not found"
