"""Exercise only an isolated iron-pulse-check-* Compose project.

Start the stack first, then set COMPOSE_PROJECT_NAME, COMPOSE_FILE and HTTP_PORT.
This script creates temporary accounts and data and restarts its API container.
"""

from datetime import date
import json
import os
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT = os.environ.get("COMPOSE_PROJECT_NAME", "")
BASE = "http://127.0.0.1:" + os.environ.get("HTTP_PORT", "18080")
PASSWORD = "Docker-check-password-2026!"


def compose(*args, input_text=None):
    result = subprocess.run(
        ["docker", "compose", *args], input=input_text,
        text=True, capture_output=True, timeout=120,
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout


def request(path, method="GET", data=None, token=None, expected=200, form=False):
    headers = {}
    if data is None:
        body = None
    elif form:
        body = urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(BASE + path, data=body, headers=headers, method=method)
    try:
        response = urlopen(req, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        content = response.read()
        assert response.status == expected, f"{method} {path}: expected {expected}, got {response.status}"
        if "application/json" in response.headers.get("Content-Type", ""):
            return json.loads(content)
        return content


def main():
    if not PROJECT.startswith("iron-pulse-check-"):
        raise SystemExit("Refusing to create test data outside an iron-pulse-check-* project")
    request("/healthz", expected=204)
    assert b"Iron Pulse" in request("/")
    assert b"{" in request("/css/styles.css")
    assert request("/assets/img/iron-pulse-logo.png").startswith(b"\x89PNG")
    assert b"apiRequest" in request("/js/api.js")
    assert b"swagger" in request("/api/docs").lower()
    assert "/api/v1/auth/token" in request("/api/openapi.json")["paths"]
    assert request("/api/health")["status"] == "ok"
    for path in ("/.env", "/.git/config", "/missing-asset.css", "/main.py"):
        request(path, expected=404)
    request("/api/v1/members/", expected=401)

    compose("exec", "-T", "api", "python", "-c", """
import json, sys
from sqlmodel import Session
from app.scripts.create_admin import create_initial_admin
from app.db.session import get_engine
from app.schemas.user import UserCreate
with Session(get_engine()) as session:
    create_initial_admin(session, UserCreate(**json.load(sys.stdin)))
""", input_text=json.dumps({"username": "docker-check-admin", "password": PASSWORD}))
    token = request("/api/v1/auth/token", "POST", {
        "username": "docker-check-admin", "password": PASSWORD,
    }, form=True)["access_token"]
    plan = request("/api/v1/plans/", "POST", {
        "name": "Docker check monthly", "price": 20, "duration_days": 30,
    }, token, expected=201)
    member = request("/api/v1/members/", "POST", {
        "first_name": "Docker", "last_name": "Check", "email": "docker.check@example.test",
    }, token, expected=201)
    membership = request("/api/v1/memberships/", "POST", {
        "member_id": member["id"], "plan_id": plan["id"], "start_date": str(date.today()),
    }, token, expected=201)
    payment = request("/api/v1/payments/", "POST", {
        "membership_id": membership["id"], "amount": "20.00",
        "payment_method": "cash", "status": "completed",
    }, token, expected=201)
    assert payment["membership_id"] == membership["id"]
    request("/api/v1/reports/income", token=token)

    compose("exec", "-T", "api", "python", "-c", """
import os
from pathlib import Path
assert os.getuid() != 0
for path in ('.env', '.git', '.venv', 'app/tests', 'Frontend'):
    assert not (Path('/app') / path).exists(), path
""")
    # Recreate the DB container without dropping its volume, then restart the
    # API. Data must survive and startup must apply migrations idempotently.
    compose("up", "-d", "--force-recreate", "--wait", "--wait-timeout", "90", "db")
    compose("restart", "api")
    for attempt in range(60):
        try:
            if request("/api/health")["status"] == "ok":
                break
        except (URLError, TimeoutError, AssertionError):
            time.sleep(1)
    else:
        raise AssertionError("API did not recover after restart")
    saved = request(f"/api/v1/members/{member['id']}", token=token)
    assert saved["email"] == "docker.check@example.test"
    print("Docker deployment OK: frontend, proxy, login, PostgreSQL, persistence and image isolation")


if __name__ == "__main__":
    main()
