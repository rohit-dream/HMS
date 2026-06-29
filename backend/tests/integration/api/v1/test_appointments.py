"""Integration tests — MVP-084 appointments CRUD API."""

from __future__ import annotations

import uuid
from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.doctor_schedule_repository import DoctorScheduleRepository
from app.domains.org.repositories.staff_repository import StaffRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def receptionist_with_doctor():
    tenant_id = uuid.uuid4()
    email = f"appt-{tenant_id.hex[:8]}@example.com"
    slug = f"appt-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        location = LocationRepository(db, data["tenant_id"]).get_primary()
        assert location is not None
        dept = DepartmentRepository(db, data["tenant_id"]).create(
            name="General Medicine",
            code="GEN",
            location_id=location.id,
            is_active=True,
        )
        staff = StaffRepository(db, data["tenant_id"]).create(
            employee_code="DOC-001",
            first_name="Vikram",
            last_name="Patel",
            joining_date=date(2018, 1, 1),
            status="active",
            department_id=dept.id,
            location_id=location.id,
        )
        db.flush()
        doctor = DoctorRepository(db, data["tenant_id"]).create(
            staff_id=staff.id,
            specialization="General Medicine",
            consultation_fee=Decimal("500.00"),
            department_id=dept.id,
        )
        db.flush()
        schedule_repo = DoctorScheduleRepository(db, data["tenant_id"])
        for day in range(7):
            schedule_repo.create(
                doctor_id=doctor.id,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(18, 0),
                slot_duration_minutes=20,
                max_patients_per_slot=1,
                location_id=location.id,
                is_active=True,
            )
        db.commit()
        data["location_id"] = location.id
        data["doctor_id"] = doctor.id

    yield data


def _auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    token = resp.json()["data"]["access_token"]
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _patient_payload(**overrides: object) -> dict:
    payload = {
        "first_name": "Anita",
        "last_name": "Sharma",
        "date_of_birth": "1985-03-15",
        "gender": "female",
        "phone": "9876543210",
        **CONSENT_DEFAULTS,
    }
    payload.update(overrides)
    return payload


def _appointment_payload(
    *,
    patient_id: str,
    doctor_id: str,
    location_id: str | None = None,
    appointment_date: str | None = None,
    **overrides: object,
) -> dict:
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date or (date.today() + timedelta(days=1)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "09:20:00",
        "appointment_type": "new",
    }
    if location_id is not None:
        payload["location_id"] = location_id
    payload.update(overrides)
    return payload


def test_create_list_and_get_appointment(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    patient = client.post(
        "/api/v1/patients",
        json=_patient_payload(location_id=str(receptionist_with_doctor["location_id"])),
        headers=headers,
    )
    assert patient.status_code == status.HTTP_201_CREATED
    patient_id = patient.json()["data"]["id"]

    create = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_id,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
            location_id=str(receptionist_with_doctor["location_id"]),
            notes="Follow-up for blood pressure",
        ),
        headers=headers,
    )
    assert create.status_code == status.HTTP_201_CREATED
    created = create.json()["data"]
    assert created["patient_name"] == "Anita Sharma"
    assert created["doctor_name"] == "Dr. Vikram Patel"
    assert created["status"] == "scheduled"
    assert created["appointment_type"] == "new"
    appointment_id = created["id"]

    listing = client.get("/api/v1/appointments", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert any(item["id"] == appointment_id for item in listing.json()["data"])

    detail = client.get(f"/api/v1/appointments/{appointment_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json()["data"]["notes"] == "Follow-up for blood pressure"


def test_update_appointment(client: TestClient, receptionist_with_doctor: dict) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    patient_id = client.post(
        "/api/v1/patients",
        json=_patient_payload(),
        headers=headers,
    ).json()["data"]["id"]
    appointment_id = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_id,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
        ),
        headers=headers,
    ).json()["data"]["id"]

    new_date = (date.today() + timedelta(days=2)).isoformat()
    update = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={
            "appointment_date": new_date,
            "start_time": "10:00:00",
            "end_time": "10:20:00",
            "notes": "Rescheduled by patient request",
        },
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    data = update.json()["data"]
    assert data["appointment_date"] == new_date
    assert data["start_time"] == "10:00:00"
    assert data["notes"] == "Rescheduled by patient request"


def test_delete_appointment(client: TestClient, receptionist_with_doctor: dict) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    patient_id = client.post(
        "/api/v1/patients",
        json=_patient_payload(),
        headers=headers,
    ).json()["data"]["id"]
    appointment_id = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_id,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
        ),
        headers=headers,
    ).json()["data"]["id"]

    delete = client.delete(f"/api/v1/appointments/{appointment_id}", headers=headers)
    assert delete.status_code == status.HTTP_204_NO_CONTENT

    detail = client.get(f"/api/v1/appointments/{appointment_id}", headers=headers)
    assert detail.status_code == status.HTTP_404_NOT_FOUND


def test_list_appointments_filters(client: TestClient, receptionist_with_doctor: dict) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    patient_id = client.post(
        "/api/v1/patients",
        json=_patient_payload(),
        headers=headers,
    ).json()["data"]["id"]
    appt_date = (date.today() + timedelta(days=3)).isoformat()
    client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_id,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
            appointment_date=appt_date,
            start_time="11:00:00",
            end_time="11:20:00",
        ),
        headers=headers,
    )

    by_doctor = client.get(
        f"/api/v1/appointments?doctor_id={receptionist_with_doctor['doctor_id']}",
        headers=headers,
    )
    assert by_doctor.status_code == status.HTTP_200_OK
    assert by_doctor.json()["meta"]["pagination"]["total_items"] >= 1

    by_date = client.get(
        f"/api/v1/appointments?appointment_date={appt_date}",
        headers=headers,
    )
    assert by_date.status_code == status.HTTP_200_OK
    assert all(item["appointment_date"] == appt_date for item in by_date.json()["data"])

    by_status = client.get("/api/v1/appointments?status=scheduled", headers=headers)
    assert by_status.status_code == status.HTTP_200_OK


def test_cannot_book_past_date(client: TestClient, receptionist_with_doctor: dict) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    patient_id = client.post(
        "/api/v1/patients",
        json=_patient_payload(),
        headers=headers,
    ).json()["data"]["id"]

    resp = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_id,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
            appointment_date=(date.today() - timedelta(days=1)).isoformat(),
        ),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert resp.json()["errors"][0]["code"] == "validation_error"


def test_cannot_book_unavailable_doctor(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    with session_scope() as db:
        doctor = DoctorRepository(db, receptionist_with_doctor["tenant_id"]).get_by_id(
            receptionist_with_doctor["doctor_id"]
        )
        assert doctor is not None
        doctor.is_available = False
        db.commit()

    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    patient_id = client.post(
        "/api/v1/patients",
        json=_patient_payload(),
        headers=headers,
    ).json()["data"]["id"]

    resp = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_id,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
        ),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_double_book_returns_409(client: TestClient, receptionist_with_doctor: dict) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    patient_a = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9876543210"),
        headers=headers,
    ).json()["data"]["id"]
    patient_b = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9876543211"),
        headers=headers,
    ).json()["data"]["id"]
    appt_date = (date.today() + timedelta(days=4)).isoformat()
    slot = {
        "appointment_date": appt_date,
        "start_time": "14:00:00",
        "end_time": "14:20:00",
    }

    first = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_a,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
            **slot,
        ),
        headers=headers,
    )
    assert first.status_code == status.HTTP_201_CREATED

    second = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_b,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
            **slot,
        ),
        headers=headers,
    )
    assert second.status_code == status.HTTP_409_CONFLICT
    assert second.json()["errors"][0]["code"] == "conflict"


def test_appointment_tenant_isolation(client: TestClient, receptionist_with_doctor: dict) -> None:
    headers_a = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    patient_id = client.post(
        "/api/v1/patients",
        json=_patient_payload(),
        headers=headers_a,
    ).json()["data"]["id"]
    appointment_id = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_id,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
        ),
        headers=headers_a,
    ).json()["data"]["id"]

    tenant_b = uuid.uuid4()
    with session_scope() as db:
        data_b = provision_tenant_with_role(
            db,
            slug=f"appt-b-{tenant_b.hex[:8]}",
            email=f"appt-b-{tenant_b.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    headers_b = _auth_headers(client, data_b["slug"], data_b["email"])
    resp = client.get(f"/api/v1/appointments/{appointment_id}", headers=headers_b)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_nurse_cannot_create_appointment(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    email = f"nurse-{tenant_id.hex[:8]}@example.com"
    slug = f"nurse-{tenant_id.hex[:8]}"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="nurse",
        )
        db.commit()

    headers = _auth_headers(client, slug, email)
    resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": str(uuid.uuid4()),
            "doctor_id": str(uuid.uuid4()),
            "appointment_date": (date.today() + timedelta(days=1)).isoformat(),
            "start_time": "09:00:00",
            "end_time": "09:20:00",
            "appointment_type": "new",
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def _book_appointment(
    client: TestClient,
    headers: dict[str, str],
    receptionist_with_doctor: dict,
    *,
    start_time: str = "09:00:00",
    end_time: str = "09:20:00",
    phone: str = "9876543210",
) -> str:
    patient_id = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone=phone),
        headers=headers,
    ).json()["data"]["id"]
    appointment_id = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(
            patient_id=patient_id,
            doctor_id=str(receptionist_with_doctor["doctor_id"]),
            start_time=start_time,
            end_time=end_time,
        ),
        headers=headers,
    ).json()["data"]["id"]
    return appointment_id


def test_confirm_scheduled_appointment(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    appointment_id = _book_appointment(client, headers, receptionist_with_doctor)

    resp = client.post(f"/api/v1/appointments/{appointment_id}/confirm", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["status"] == "confirmed"


def test_cannot_confirm_non_scheduled_appointment(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    appointment_id = _book_appointment(client, headers, receptionist_with_doctor)
    client.post(f"/api/v1/appointments/{appointment_id}/confirm", headers=headers)

    resp = client.post(f"/api/v1/appointments/{appointment_id}/confirm", headers=headers)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_cancel_appointment_with_reason(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    appointment_id = _book_appointment(client, headers, receptionist_with_doctor)

    resp = client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancelled_reason": "Patient requested cancellation"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["status"] == "cancelled"
    assert data["cancelled_reason"] == "Patient requested cancellation"


def test_cancel_confirmed_appointment(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    appointment_id = _book_appointment(
        client,
        headers,
        receptionist_with_doctor,
        phone="9876543212",
        start_time="09:20:00",
        end_time="09:40:00",
    )
    client.post(f"/api/v1/appointments/{appointment_id}/confirm", headers=headers)

    resp = client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancelled_reason": "Doctor unavailable"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["status"] == "cancelled"


def test_cannot_cancel_without_reason(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    appointment_id = _book_appointment(
        client,
        headers,
        receptionist_with_doctor,
        phone="9876543213",
        start_time="09:40:00",
        end_time="10:00:00",
    )

    resp = client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancelled_reason": "   "},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_cannot_cancel_already_cancelled(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = _auth_headers(
        client,
        receptionist_with_doctor["slug"],
        receptionist_with_doctor["email"],
    )
    appointment_id = _book_appointment(
        client,
        headers,
        receptionist_with_doctor,
        phone="9876543214",
        start_time="10:00:00",
        end_time="10:20:00",
    )
    client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancelled_reason": "Patient no-show risk"},
        headers=headers,
    )

    resp = client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancelled_reason": "Duplicate cancel"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
