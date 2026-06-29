"""Integration tests — MVP-096 OPD queue polling endpoint."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.opd_api import auth_headers, provision_receptionist_with_doctor
from tests.integration.api.v1.test_opd_queue import _create_queued_visit

pytestmark = pytest.mark.integration


def test_poll_queue_returns_etag_and_interval(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])
    _create_queued_visit(
        client,
        headers,
        doctor_id=doctor_id,
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )

    resp = client.get(
        "/api/v1/opd/queue/poll",
        params={"doctor_id": doctor_id, "date": date.today().isoformat()},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK, resp.text
    assert resp.headers.get("etag")
    data = resp.json()["data"]
    assert data["poll_interval_seconds"] == 5
    assert data["changed"] is True
    assert data["etag"] == resp.headers["etag"].strip('"')


def test_poll_returns_304_when_etag_unchanged(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])
    _create_queued_visit(
        client,
        headers,
        doctor_id=doctor_id,
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )
    params = {"doctor_id": doctor_id, "date": date.today().isoformat()}

    first = client.get("/api/v1/opd/queue/poll", params=params, headers=headers)
    etag = first.headers["etag"]

    second = client.get(
        "/api/v1/opd/queue/poll",
        params=params,
        headers={**headers, "If-None-Match": etag},
    )
    assert second.status_code == status.HTTP_304_NOT_MODIFIED
    assert second.headers.get("etag") == etag


def test_poll_etag_changes_after_call(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])
    visit = _create_queued_visit(
        client,
        headers,
        doctor_id=doctor_id,
        location_id=str(ctx["location_id"]),
        phone_suffix=uuid.uuid4().int % 100000,
    )
    params = {"doctor_id": doctor_id, "date": date.today().isoformat()}

    before = client.get("/api/v1/opd/queue/poll", params=params, headers=headers)
    etag_before = before.headers["etag"]

    called = client.post(f"/api/v1/opd/queue/{visit['queue_id']}/call", headers=headers)
    assert called.status_code == status.HTTP_200_OK

    after = client.get(
        "/api/v1/opd/queue/poll",
        params=params,
        headers={**headers, "If-None-Match": etag_before},
    )
    assert after.status_code == status.HTTP_200_OK
    assert after.headers["etag"] != etag_before
    assert after.json()["data"]["entries"][0]["status"] == "called"
