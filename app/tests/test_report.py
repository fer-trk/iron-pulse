import pytest

pytestmark = pytest.mark.usefixtures("auth_headers")


def test_empty_income_report(client):
    response = client.get("/api/v1/reports/income")
    assert response.status_code == 200
    assert response.json()["total_income"] == "0.00"
    assert response.json()["total_payments"] == 0


def test_income_rejects_invalid_range(client):
    assert client.get("/api/v1/reports/income?start_date=2026-05-31&end_date=2026-05-01").status_code == 400


@pytest.mark.parametrize("path", ["/api/v1/attendances/", "/api/v1/reports/attendance"])
def test_attendance_features_are_not_exposed(client, path):
    assert client.get(path).status_code == 404
