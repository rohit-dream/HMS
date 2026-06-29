"""SQLAlchemy ORM — import Base for Alembic; business models added in later migrations."""

from app.models.base import (
    AuditMixin,
    Base,
    ImmutableTenantEntity,
    SoftDeleteMixin,
    TenantAuditableEntity,
    TenantMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    active_row_filter,
)
from app.models.audit.audit_log import AuditLog
from app.models.clinical.appointment import Appointment
from app.models.clinical.opd import (
    OpdClinicalNote,
    OpdPrescription,
    OpdPrescriptionItem,
    OpdQueue,
    OpdReferral,
    OpdVitals,
    OpdVisit,
)
from app.models.core.department import Department
from app.models.core.doctor import Doctor
from app.models.core.doctor_schedule import DoctorSchedule
from app.models.core.email_verification_token import EmailVerificationToken
from app.models.core.password_reset_token import PasswordResetToken
from app.models.core.patient import Patient
from app.models.core.patient_allergy import PatientAllergy
from app.models.core.patient_contact import PatientContact
from app.models.core.patient_document import PatientDocument
from app.models.core.permission import Permission
from app.models.core.role import Role
from app.models.core.role_permission import RolePermission
from app.models.core.staff import Staff
from app.models.core.user import User
from app.models.core.user_invite_token import UserInviteToken
from app.models.core.user_role import UserRole
from app.models.core.user_session import UserSession
from app.models.platform.tenant import Tenant
from app.models.platform.tenant_location import TenantLocation
from app.models.platform.tenant_setting import TenantSetting

__all__ = [
    "AuditLog",
    "Appointment",
    "OpdClinicalNote",
    "OpdPrescription",
    "OpdPrescriptionItem",
    "OpdQueue",
    "OpdReferral",
    "OpdVitals",
    "OpdVisit",
    "AuditMixin",
    "Base",
    "ImmutableTenantEntity",
    "Patient",
    "PatientAllergy",
    "PatientContact",
    "PatientDocument",
    "Permission",
    "Department",
    "Doctor",
    "DoctorSchedule",
    "EmailVerificationToken",
    "PasswordResetToken",
    "Role",
    "RolePermission",
    "Staff",
    "SoftDeleteMixin",
    "Tenant",
    "TenantAuditableEntity",
    "TenantLocation",
    "TenantMixin",
    "TenantSetting",
    "TimestampMixin",
    "User",
    "UserInviteToken",
    "UserRole",
    "UserSession",
    "UUIDPrimaryKeyMixin",
    "active_row_filter",
]
