"""
MVP-068 — Org cross-tenant isolation regression (Sprint 6).

Verifies Tenant B cannot read or mutate Tenant A org data across:
- PostgreSQL RLS (core org tables)
- Org domain repositories
- Org HTTP APIs (departments, staff, doctors, schedules)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import CORE_ORG_RLS_TABLES
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.doctor_schedule_repository import DoctorScheduleRepository
from app.domains.org.repositories.staff_repository import StaffRepository
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


@dataclass(frozen=True)
class OrgIsolationFixture:
    slug_a: str
    email_a: str
    slug_b: str
    email_b: str
    tenant_a_id: uuid.UUID
    tenant_b_id: uuid.UUID
    department_id: uuid.UUID
    staff_id: uuid.UUID
    doctor_id: uuid.UUID
    schedule_id: uuid.UUID
    department_code: str
    employee_code: str


@pytest.fixture(scope="module")
def org_pair() -> OrgIsolationFixture:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"org-iso-a-{suffix_a}"
    slug_b = f"org-iso-b-{suffix_b}"
    email_a = f"org-iso-a-{suffix_a}@example.com"
    email_b = f"org-iso-b-{suffix_b}@example.com"
    department_code = f"SEC-{suffix_a.upper()}"
    employee_code = f"EMP-{suffix_a.upper()}"

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=slug_a,
            email=email_a,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        data_b = provision_tenant_with_role(
            db,
            slug=slug_b,
            email=email_b,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

        dept = DepartmentRepository(db, data_a["tenant_id"]).create(
            name="Tenant A Secret Department",
            code=department_code,
            is_active=True,
        )
        staff = StaffRepository(db, data_a["tenant_id"]).create(
            employee_code=employee_code,
            first_name="Secret",
            last_name="Staff",
            joining_date=date.today(),
            status="active",
            department_id=dept.id,
        )
        db.flush()
        doctor = DoctorRepository(db, data_a["tenant_id"]).create(
            staff_id=staff.id,
            specialization="Hidden Specialty",
            consultation_fee=Decimal("500.00"),
            department_id=dept.id,
        )
        db.flush()
        schedule = DoctorScheduleRepository(db, data_a["tenant_id"]).create(
            doctor_id=doctor.id,
            day_of_week=2,
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration_minutes=20,
        )
        db.commit()

        return OrgIsolationFixture(
            slug_a=slug_a,
            email_a=email_a,
            slug_b=slug_b,
            email_b=email_b,
            tenant_a_id=data_a["tenant_id"],
            tenant_b_id=data_b["tenant_id"],
            department_id=dept.id,
            staff_id=staff.id,
            doctor_id=doctor.id,
            schedule_id=schedule.id,
            department_code=department_code,
            employee_code=employee_code,
        )


def _auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK, resp.text
    token = resp.json()["data"]["access_token"]
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _assert_hidden_under_rls(
    db,
    *,
    viewer_tenant_id: uuid.UUID,
    sql: str,
    params: dict,
) -> None:
    use_rls_enforced_role(db)
    set_rls_tenant_context(db, viewer_tenant_id)
    count = db.execute(text(sql), params).scalar_one()
    assert count == 0, f"Expected 0 rows for tenant {viewer_tenant_id}, got {count}"


class TestOrgRlsIsolation:
    """Direct SQL under hms_app — all core org tables."""

    @pytest.mark.parametrize("table", CORE_ORG_RLS_TABLES)
    def test_org_tables_have_force_rls(self, table: str) -> None:
        with session_scope() as db:
            row = db.execute(
                text(
                    """
                    SELECT c.relrowsecurity, c.relforcerowsecurity
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'core' AND c.relname = :table
                    """
                ),
                {"table": table},
            ).one()
            assert row[0] is True, f"{table}: RLS not enabled"
            assert row[1] is True, f"{table}: FORCE RLS not enabled"

    def test_tenant_b_cannot_see_tenant_a_org_rows(self, org_pair: OrgIsolationFixture) -> None:
        cases = [
            (
                "SELECT COUNT(*) FROM core.departments WHERE id = :id",
                {"id": org_pair.department_id},
            ),
            (
                "SELECT COUNT(*) FROM core.staff WHERE id = :id",
                {"id": org_pair.staff_id},
            ),
            (
                "SELECT COUNT(*) FROM core.doctors WHERE id = :id",
                {"id": org_pair.doctor_id},
            ),
            (
                "SELECT COUNT(*) FROM core.doctor_schedules WHERE id = :id",
                {"id": org_pair.schedule_id},
            ),
        ]
        with session_scope() as db:
            for sql, params in cases:
                _assert_hidden_under_rls(
                    db,
                    viewer_tenant_id=org_pair.tenant_b_id,
                    sql=sql,
                    params=params,
                )


class TestOrgRepositoryIsolation:
    """Org repositories must not return cross-tenant rows."""

    def test_department_repository_isolated(self, org_pair: OrgIsolationFixture) -> None:
        with session_scope() as db:
            use_rls_enforced_role(db)
            repo_b = DepartmentRepository(db, org_pair.tenant_b_id)
            assert repo_b.get_by_id(org_pair.department_id) is None
            assert repo_b.get_by_code(org_pair.department_code) is None

    def test_staff_repository_isolated(self, org_pair: OrgIsolationFixture) -> None:
        with session_scope() as db:
            use_rls_enforced_role(db)
            repo_b = StaffRepository(db, org_pair.tenant_b_id)
            assert repo_b.get_by_id(org_pair.staff_id) is None
            assert repo_b.get_by_employee_code(org_pair.employee_code) is None

    def test_doctor_repository_isolated(self, org_pair: OrgIsolationFixture) -> None:
        with session_scope() as db:
            use_rls_enforced_role(db)
            repo_b = DoctorRepository(db, org_pair.tenant_b_id)
            assert repo_b.get_by_id(org_pair.doctor_id) is None
            assert repo_b.get_by_staff_id(org_pair.staff_id) is None

    def test_schedule_repository_isolated(self, org_pair: OrgIsolationFixture) -> None:
        with session_scope() as db:
            use_rls_enforced_role(db)
            repo_b = DoctorScheduleRepository(db, org_pair.tenant_b_id)
            assert repo_b.get_by_id(org_pair.schedule_id) is None
            assert (
                repo_b.get_for_doctor(org_pair.doctor_id, org_pair.schedule_id) is None
            )


class TestOrgApiIsolation:
    """Authenticated org APIs must scope all reads/writes to JWT tenant."""

    def test_cannot_read_other_tenant_org_resources(
        self, client: TestClient, org_pair: OrgIsolationFixture
    ) -> None:
        headers_b = _auth_headers(client, org_pair.slug_b, org_pair.email_b)
        assert (
            client.get(
                f"/api/v1/admin/departments/{org_pair.department_id}",
                headers=headers_b,
            ).status_code
            == 404
        )
        assert (
            client.get(f"/api/v1/staff/{org_pair.staff_id}", headers=headers_b).status_code
            == 404
        )
        assert (
            client.get(f"/api/v1/doctors/{org_pair.doctor_id}", headers=headers_b).status_code
            == 404
        )
        assert (
            client.get(
                f"/api/v1/doctors/{org_pair.doctor_id}/schedules/{org_pair.schedule_id}",
                headers=headers_b,
            ).status_code
            == 404
        )

    def test_cannot_mutate_other_tenant_org_resources(
        self, client: TestClient, org_pair: OrgIsolationFixture
    ) -> None:
        headers_b = _auth_headers(client, org_pair.slug_b, org_pair.email_b)
        assert (
            client.patch(
                f"/api/v1/admin/departments/{org_pair.department_id}",
                json={"name": "Hijacked"},
                headers=headers_b,
            ).status_code
            == 404
        )
        assert (
            client.patch(
                f"/api/v1/staff/{org_pair.staff_id}",
                json={"first_name": "Hijacked"},
                headers=headers_b,
            ).status_code
            == 404
        )
        assert (
            client.patch(
                f"/api/v1/doctors/{org_pair.doctor_id}",
                json={"specialization": "Hijacked"},
                headers=headers_b,
            ).status_code
            == 404
        )
        assert (
            client.patch(
                f"/api/v1/doctors/{org_pair.doctor_id}/schedules/{org_pair.schedule_id}",
                json={"end_time": "18:00:00"},
                headers=headers_b,
            ).status_code
            == 404
        )
        assert (
            client.delete(
                f"/api/v1/admin/departments/{org_pair.department_id}",
                headers=headers_b,
            ).status_code
            == 404
        )
        assert (
            client.delete(f"/api/v1/staff/{org_pair.staff_id}", headers=headers_b).status_code
            == 404
        )
        assert (
            client.delete(f"/api/v1/doctors/{org_pair.doctor_id}", headers=headers_b).status_code
            == 404
        )
        assert (
            client.delete(
                f"/api/v1/doctors/{org_pair.doctor_id}/schedules/{org_pair.schedule_id}",
                headers=headers_b,
            ).status_code
            == 404
        )

    def test_org_list_endpoints_exclude_other_tenant_data(
        self, client: TestClient, org_pair: OrgIsolationFixture
    ) -> None:
        headers_b = _auth_headers(client, org_pair.slug_b, org_pair.email_b)

        dept_resp = client.get("/api/v1/admin/departments", headers=headers_b)
        assert dept_resp.status_code == status.HTTP_200_OK
        dept_ids = {item["id"] for item in dept_resp.json()["data"]}
        dept_codes = {item["code"] for item in dept_resp.json()["data"]}
        assert str(org_pair.department_id) not in dept_ids
        assert org_pair.department_code not in dept_codes

        staff_resp = client.get("/api/v1/staff", headers=headers_b)
        assert staff_resp.status_code == status.HTTP_200_OK
        staff_ids = {item["id"] for item in staff_resp.json()["data"]}
        staff_codes = {item["employee_code"] for item in staff_resp.json()["data"]}
        assert str(org_pair.staff_id) not in staff_ids
        assert org_pair.employee_code not in staff_codes

        doctors_resp = client.get("/api/v1/doctors", headers=headers_b)
        assert doctors_resp.status_code == status.HTTP_200_OK
        doctor_ids = {item["id"] for item in doctors_resp.json()["data"]}
        assert str(org_pair.doctor_id) not in doctor_ids

        schedules_resp = client.get(
            f"/api/v1/doctors/{org_pair.doctor_id}/schedules",
            headers=headers_b,
        )
        assert schedules_resp.status_code == 404

    def test_tenant_a_retains_access_to_own_org_resources(
        self, client: TestClient, org_pair: OrgIsolationFixture
    ) -> None:
        headers_a = _auth_headers(client, org_pair.slug_a, org_pair.email_a)
        assert (
            client.get(
                f"/api/v1/admin/departments/{org_pair.department_id}",
                headers=headers_a,
            ).status_code
            == 200
        )
        assert (
            client.get(f"/api/v1/staff/{org_pair.staff_id}", headers=headers_a).status_code
            == 200
        )
        assert (
            client.get(f"/api/v1/doctors/{org_pair.doctor_id}", headers=headers_a).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/doctors/{org_pair.doctor_id}/schedules/{org_pair.schedule_id}",
                headers=headers_a,
            ).status_code
            == 200
        )
