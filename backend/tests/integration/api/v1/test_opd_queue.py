"""Integration tests — MVP-093 OPD queue API."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.opd_api import (
    auth_headers,
    create_patient,
    create_visit,
    provision_doctor_user,
    provision_receptionist_with_doctor,
)
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


def _create_queued_visit(
    client: TestClient,
    headers: dict[str, str],
    *,
    doctor_id: str,
    location_id: str,
    phone_suffix: int,
) -> dict:
    patient_id = create_patient(
        client,
        headers,
        phone=f"98765{phone_suffix:05d}",
    )
    resp = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=doctor_id,
        location_id=location_id,
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    return resp.json()["data"]


def test_get_queue_board_lists_waiting_patients(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])

    first = _create_queued_visit(
        client,
        headers,
        doctor_id=doctor_id,
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )
    second = _create_queued_visit(
        client,
        headers,
        doctor_id=doctor_id,
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )

    board = client.get(
        "/api/v1/opd/queue",
        params={"doctor_id": doctor_id, "date": date.today().isoformat()},
        headers=headers,
    )
    assert board.status_code == status.HTTP_200_OK, board.text
    data = board.json()["data"]
    assert data["waiting_count"] == 2
    assert len(data["entries"]) == 2
    tokens = [entry["token_number"] for entry in data["entries"]]
    assert tokens == [1, 2]
    assert {entry["opd_visit_id"] for entry in data["entries"]} == {first["id"], second["id"]}


def test_add_visit_to_queue_manually(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
        add_to_queue=False,
    )
    assert visit.status_code == status.HTTP_201_CREATED
    visit_id = visit.json()["data"]["id"]

    queued = client.post(
        "/api/v1/opd/queue",
        json={"opd_visit_id": visit_id, "priority": "urgent"},
        headers=headers,
    )
    assert queued.status_code == status.HTTP_201_CREATED, queued.text
    body = queued.json()["data"]
    assert body["token_number"] == 1
    assert body["priority"] == "urgent"
    assert body["status"] == "waiting"


def test_duplicate_queue_add_returns_409(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    visit = _create_queued_visit(
        client,
        headers,
        doctor_id=str(ctx["doctor_id"]),
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )

    duplicate = client.post(
        "/api/v1/opd/queue",
        json={"opd_visit_id": visit["id"]},
        headers=headers,
    )
    assert duplicate.status_code == status.HTTP_409_CONFLICT
    assert duplicate.json()["errors"][0]["field"] == "opd_visit_id"


def test_call_and_complete_queue_entry(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    visit = _create_queued_visit(
        client,
        headers,
        doctor_id=str(ctx["doctor_id"]),
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )
    queue_id = visit["queue_id"]

    called = client.post(f"/api/v1/opd/queue/{queue_id}/call", headers=headers)
    assert called.status_code == status.HTTP_200_OK
    assert called.json()["data"]["status"] == "called"
    assert called.json()["data"]["called_at"] is not None

    board = client.get(
        "/api/v1/opd/queue",
        params={"doctor_id": str(ctx["doctor_id"]), "date": date.today().isoformat()},
        headers=headers,
    )
    assert board.json()["data"]["current_token"] == 1

    completed = client.post(f"/api/v1/opd/queue/{queue_id}/complete", headers=headers)
    assert completed.status_code == status.HTTP_200_OK
    assert completed.json()["data"]["status"] == "completed"


def test_skip_renumbers_waiting_tokens(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])

    visits = [
        _create_queued_visit(
            client,
            headers,
            doctor_id=doctor_id,
            location_id=str(ctx["location_id"]),
            phone_suffix=uuid.uuid4().int % 100000,
        )
        for _ in range(3)
    ]

    skipped = client.post(
        f"/api/v1/opd/queue/{visits[0]['queue_id']}/skip",
        json={"reason": "Patient stepped out"},
        headers=headers,
    )
    assert skipped.status_code == status.HTTP_200_OK
    assert skipped.json()["data"]["status"] == "skipped"

    board = client.get(
        "/api/v1/opd/queue",
        params={"doctor_id": doctor_id, "date": date.today().isoformat()},
        headers=headers,
    )
    waiting_tokens = [
        entry["token_number"]
        for entry in board.json()["data"]["entries"]
        if entry["status"] == "waiting"
    ]
    assert waiting_tokens == [1, 2]


def test_reorder_waiting_queue_entry(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])

    visits = [
        _create_queued_visit(
            client,
            headers,
            doctor_id=doctor_id,
            location_id=str(ctx["location_id"]),
            phone_suffix=uuid.uuid4().int % 100000,
        )
        for _ in range(3)
    ]
    last_queue_id = visits[2]["queue_id"]

    moved = client.patch(
        f"/api/v1/opd/queue/{last_queue_id}",
        json={"position": 1},
        headers=headers,
    )
    assert moved.status_code == status.HTTP_200_OK
    assert moved.json()["data"]["token_number"] == 1

    board = client.get(
        "/api/v1/opd/queue",
        params={"doctor_id": doctor_id, "date": date.today().isoformat()},
        headers=headers,
    )
    waiting_tokens = [
        entry["token_number"]
        for entry in board.json()["data"]["entries"]
        if entry["status"] == "waiting"
    ]
    assert waiting_tokens == [1, 2, 3]


def test_cross_tenant_queue_entry_returns_404(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    visit = _create_queued_visit(
        client,
        headers,
        doctor_id=str(ctx["doctor_id"]),
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )

    other = uuid.uuid4()
    with session_scope() as db:
        tenant = provision_tenant_with_role(
            db,
            slug=f"queue-iso-{other.hex[:8]}",
            email=f"queue-iso-{other.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    other_headers = auth_headers(client, tenant["slug"], tenant["email"])
    resp = client.post(
        f"/api/v1/opd/queue/{visit['queue_id']}/call",
        headers=other_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_requeue_visit_after_skip(client: TestClient) -> None:
    """Skipped visits may be added back to the active queue with a new token."""
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    visit = _create_queued_visit(
        client,
        headers,
        doctor_id=str(ctx["doctor_id"]),
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )

    skipped = client.post(
        f"/api/v1/opd/queue/{visit['queue_id']}/skip",
        json={"reason": "Patient stepped out"},
        headers=headers,
    )
    assert skipped.status_code == status.HTTP_200_OK

    requeued = client.post(
        "/api/v1/opd/queue",
        json={"opd_visit_id": visit["id"], "priority": "urgent"},
        headers=headers,
    )
    assert requeued.status_code == status.HTTP_201_CREATED, requeued.text
    body = requeued.json()["data"]
    assert body["status"] == "waiting"
    assert body["priority"] == "urgent"
    assert body["id"] != visit["queue_id"]
    # Next token uses max existing token for doctor/date (skipped entry still counts).
    assert body["token_number"] == 2


def test_doctor_without_queue_permission_gets_403(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    doctor_email = provision_doctor_user(ctx)
    doctor_headers = auth_headers(client, ctx["slug"], doctor_email)

    resp = client.get(
        "/api/v1/opd/queue",
        params={"doctor_id": str(ctx["doctor_id"]), "date": date.today().isoformat()},
        headers=doctor_headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_call_non_waiting_patient_returns_409(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    visit = _create_queued_visit(
        client,
        headers,
        doctor_id=str(ctx["doctor_id"]),
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )
    queue_id = visit["queue_id"]

    first = client.post(f"/api/v1/opd/queue/{queue_id}/call", headers=headers)
    assert first.status_code == status.HTTP_200_OK

    second = client.post(f"/api/v1/opd/queue/{queue_id}/call", headers=headers)
    assert second.status_code == status.HTTP_409_CONFLICT
    assert second.json()["errors"][0]["field"] == "status"


def test_reorder_non_waiting_entry_returns_409(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    visit = _create_queued_visit(
        client,
        headers,
        doctor_id=str(ctx["doctor_id"]),
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )
    queue_id = visit["queue_id"]

    called = client.post(f"/api/v1/opd/queue/{queue_id}/call", headers=headers)
    assert called.status_code == status.HTTP_200_OK

    moved = client.patch(
        f"/api/v1/opd/queue/{queue_id}",
        json={"position": 1},
        headers=headers,
    )
    assert moved.status_code == status.HTTP_409_CONFLICT
    assert moved.json()["errors"][0]["field"] == "status"


def test_add_unknown_visit_to_queue_returns_404(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])

    resp = client.post(
        "/api/v1/opd/queue",
        json={"opd_visit_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["errors"][0]["field"] == "opd_visit_id"
