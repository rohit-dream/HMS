"""Patient visit history — reads from clinical.opd_visits when available."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app.domains.patients.schemas.visit_history import PatientVisitHistoryItem
from app.repositories.base import TenantScopedRepository

_OPD_VISITS_TABLE = "opd_visits"
_CLINICAL_NOTES_TABLE = "opd_clinical_notes"


class PatientVisitHistoryRepository(TenantScopedRepository):
    def opd_visits_available(self) -> bool:
        return self.db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'clinical'
                      AND table_name = :table_name
                )
                """
            ),
            {"table_name": _OPD_VISITS_TABLE},
        ).scalar_one()

    def _clinical_notes_available(self) -> bool:
        return self.db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'clinical'
                      AND table_name = :table_name
                )
                """
            ),
            {"table_name": _CLINICAL_NOTES_TABLE},
        ).scalar_one()

    def list_for_patient(
        self,
        patient_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PatientVisitHistoryItem], int]:
        if not self.opd_visits_available():
            return [], 0

        offset = (page - 1) * page_size
        params = {
            "tenant_id": self.tenant_id,
            "patient_id": patient_id,
            "limit": page_size,
            "offset": offset,
        }

        diagnosis_select = (
            """
            (
                SELECT n.content
                FROM clinical.opd_clinical_notes n
                WHERE n.tenant_id = v.tenant_id
                  AND n.opd_visit_id = v.id
                  AND n.note_type = 'diagnosis'
                  AND n.deleted_at IS NULL
                ORDER BY n.created_at DESC
                LIMIT 1
            ) AS diagnosis
            """
            if self._clinical_notes_available()
            else "NULL::text AS diagnosis"
        )

        count_sql = text(
            """
            SELECT COUNT(*)
            FROM clinical.opd_visits v
            WHERE v.tenant_id = :tenant_id
              AND v.patient_id = :patient_id
              AND v.deleted_at IS NULL
            """
        )
        total = self.db.execute(count_sql, params).scalar_one() or 0

        rows = self.db.execute(
            text(
                f"""
                SELECT
                    v.id,
                    v.visit_number,
                    v.visit_date,
                    v.status,
                    v.chief_complaint,
                    v.doctor_id,
                    TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) AS doctor_name,
                    dept.name AS department_name,
                    {diagnosis_select}
                FROM clinical.opd_visits v
                JOIN core.doctors d
                  ON d.tenant_id = v.tenant_id AND d.id = v.doctor_id
                JOIN core.staff s
                  ON s.tenant_id = d.tenant_id AND s.id = d.staff_id
                LEFT JOIN core.departments dept
                  ON dept.tenant_id = d.tenant_id AND dept.id = d.department_id
                WHERE v.tenant_id = :tenant_id
                  AND v.patient_id = :patient_id
                  AND v.deleted_at IS NULL
                ORDER BY v.visit_date DESC, v.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        ).mappings().all()

        items = [
            PatientVisitHistoryItem(
                id=row["id"],
                visit_type="opd",
                reference_number=row["visit_number"],
                visit_date=row["visit_date"],
                status=row["status"],
                doctor_id=row["doctor_id"],
                doctor_name=row["doctor_name"],
                chief_complaint=row["chief_complaint"],
                diagnosis=row["diagnosis"],
                department_name=row["department_name"],
            )
            for row in rows
        ]
        return items, int(total)

    def latest_visit_date(self, patient_id: uuid.UUID):
        if not self.opd_visits_available():
            return None

        return self.db.execute(
            text(
                """
                SELECT v.visit_date
                FROM clinical.opd_visits v
                WHERE v.tenant_id = :tenant_id
                  AND v.patient_id = :patient_id
                  AND v.deleted_at IS NULL
                  AND v.status = 'completed'
                ORDER BY v.visit_date DESC, v.completed_at DESC NULLS LAST
                LIMIT 1
                """
            ),
            {"tenant_id": self.tenant_id, "patient_id": patient_id},
        ).scalar_one_or_none()
