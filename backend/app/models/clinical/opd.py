"""clinical schema OPD tables — visits, queue, vitals, notes, prescriptions, referrals."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class OpdVisit(TenantAuditableEntity):
    __tablename__ = "opd_visits"
    __table_args__ = {"schema": "clinical"}

    visit_number: Mapped[str] = mapped_column(String(20), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    visit_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="waiting")
    token_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OpdQueue(TenantAuditableEntity):
    __tablename__ = "opd_queue"
    __table_args__ = {"schema": "clinical"}

    opd_visit_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    token_number: Mapped[int] = mapped_column(Integer, nullable=False)
    queue_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="waiting")
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="normal")
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OpdVitals(TenantAuditableEntity):
    __tablename__ = "opd_vitals"
    __table_args__ = {"schema": "clinical"}

    opd_visit_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    blood_pressure_systolic: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    blood_pressure_diastolic: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    pulse_rate: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    respiratory_rate: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    spo2: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    bmi: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class OpdClinicalNote(TenantAuditableEntity):
    __tablename__ = "opd_clinical_notes"
    __table_args__ = {"schema": "clinical"}

    opd_visit_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    note_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    icd_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    icd_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class OpdPrescription(TenantAuditableEntity):
    __tablename__ = "opd_prescriptions"
    __table_args__ = {"schema": "clinical"}

    opd_visit_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    prescription_number: Mapped[str] = mapped_column(String(20), nullable=False)
    prescribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class OpdPrescriptionItem(TenantAuditableEntity):
    __tablename__ = "opd_prescription_items"
    __table_args__ = {"schema": "clinical"}

    prescription_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    medicine_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    medicine_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), nullable=False)
    route: Mapped[str | None] = mapped_column(String(50), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)


class OpdReferral(TenantAuditableEntity):
    __tablename__ = "opd_referrals"
    __table_args__ = {"schema": "clinical"}

    opd_visit_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    referring_doctor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    referred_doctor_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    referral_type: Mapped[str] = mapped_column(String(20), nullable=False)
    external_facility: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[str] = mapped_column(String(10), nullable=False, default="routine")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
