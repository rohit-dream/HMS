"""
RBAC permission catalog and role-permission mappings.

Source: RBAC_DESIGN.md §3–§6
"""

from __future__ import annotations

# (code, display_name, module)
PERMISSION_CATALOG: tuple[tuple[str, str, str], ...] = (
    # Patient
    ("patient:read", "View Patients", "patient"),
    ("patient:create", "Register Patients", "patient"),
    ("patient:update", "Edit Patients", "patient"),
    ("patient:delete", "Deactivate Patients", "patient"),
    ("patient:export", "Export Patients", "patient"),
    # Appointments
    ("appointment:read", "View Appointments", "appointment"),
    ("appointment:create", "Book Appointments", "appointment"),
    ("appointment:update", "Update Appointments", "appointment"),
    ("appointment:delete", "Cancel Appointments", "appointment"),
    # OPD
    ("opd:read", "View OPD", "opd"),
    ("opd:create", "Create OPD Visit", "opd"),
    ("opd:update", "Update OPD", "opd"),
    ("opd:consult", "Conduct Consultation", "opd"),
    ("opd:prescribe", "Create Prescription", "opd"),
    ("opd:queue", "Manage OPD Queue", "opd"),
    # IPD
    ("ipd:read", "View IPD", "ipd"),
    ("ipd:admit", "Admit Patient", "ipd"),
    ("ipd:update", "Update IPD", "ipd"),
    ("ipd:discharge", "Discharge Patient", "ipd"),
    ("ipd:delete", "Cancel Admission", "ipd"),
    # Billing
    ("billing:read", "View Billing", "billing"),
    ("billing:create", "Create Invoice", "billing"),
    ("billing:update", "Update Invoice", "billing"),
    ("billing:delete", "Delete Invoice", "billing"),
    ("billing:void", "Void Invoice", "billing"),
    ("billing:collect", "Collect Payment", "billing"),
    ("billing:approve", "Approve Discount", "billing"),
    # Pharmacy
    ("pharmacy:read", "View Pharmacy", "pharmacy"),
    ("pharmacy:create", "Add Pharmacy Stock", "pharmacy"),
    ("pharmacy:update", "Manage Pharmacy", "pharmacy"),
    ("pharmacy:delete", "Remove Pharmacy Item", "pharmacy"),
    ("pharmacy:dispense", "Dispense Medication", "pharmacy"),
    # Laboratory
    ("laboratory:read", "View Laboratory", "laboratory"),
    ("laboratory:create", "Order Lab Test", "laboratory"),
    ("laboratory:update", "Update Lab Records", "laboratory"),
    ("laboratory:delete", "Cancel Lab Order", "laboratory"),
    ("lab:verify", "Verify Lab Results", "laboratory"),
    ("lab:report", "Finalize Lab Report", "laboratory"),
    # Platform
    ("platform:read", "View Platform", "platform"),
    ("platform:update", "Manage Platform", "platform"),
    ("platform:*", "All Platform Operations", "platform"),
    # Admin
    ("admin:users", "Manage Users", "admin"),
    ("admin:staff", "Manage Staff", "admin"),
    ("admin:departments", "Manage Departments", "admin"),
    ("admin:doctors", "Manage Doctors", "admin"),
    ("admin:settings", "Manage Settings", "admin"),
    ("admin:subscription", "Manage Subscription", "admin"),
    ("admin:impersonate", "Support Impersonation", "admin"),
    # Audit & reports
    ("audit:read", "View Audit Logs", "audit"),
    ("reports:clinical", "Clinical Reports", "reports"),
    ("reports:financial", "Financial Reports", "reports"),
    ("reports:export", "Export Reports", "reports"),
    # Wildcard
    ("*:*", "Full Tenant Access", "admin"),
)

# (code, display_name, description) — tenant-scoped roles
ROLE_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("platform_admin", "Platform Admin", "SaaS operator; platform schema only"),
    ("hospital_owner", "Hospital Owner", "Business owner; full tenant access"),
    ("hospital_admin", "Hospital Admin", "Operational administrator"),
    ("doctor", "Doctor", "Clinical consultations and prescriptions"),
    ("nurse", "Nurse", "IPD nursing and vitals"),
    ("receptionist", "Receptionist", "Front desk and appointments"),
    ("pharmacist", "Pharmacist", "Pharmacy dispensing and inventory"),
    ("lab_technician", "Lab Technician", "Laboratory processing and reports"),
    ("accountant", "Accountant", "Billing and financial reports"),
)

# Role code → permission codes (RBAC_DESIGN.md §5 CRUD matrices)
ROLE_PERMISSION_MAP: dict[str, frozenset[str]] = {
    "platform_admin": frozenset({"platform:*", "admin:impersonate"}),
    "hospital_owner": frozenset({"*:*"}),
    "hospital_admin": frozenset(
        {
            "patient:read",
            "patient:create",
            "patient:update",
            "patient:delete",
            "patient:export",
            "appointment:read",
            "appointment:create",
            "appointment:update",
            "appointment:delete",
            "opd:read",
            "opd:create",
            "opd:update",
            "opd:queue",
            "ipd:read",
            "ipd:admit",
            "ipd:update",
            "ipd:delete",
            "billing:read",
            "billing:create",
            "billing:update",
            "billing:approve",
            "pharmacy:read",
            "pharmacy:create",
            "pharmacy:update",
            "pharmacy:delete",
            "laboratory:read",
            "laboratory:create",
            "laboratory:update",
            "laboratory:delete",
            "admin:users",
            "admin:staff",
            "admin:departments",
            "admin:doctors",
            "admin:settings",
            "audit:read",
            "reports:clinical",
            "reports:export",
        }
    ),
    "doctor": frozenset(
        {
            "patient:read",
            "patient:update",
            "appointment:read",
            "opd:read",
            "opd:consult",
            "opd:prescribe",
            "ipd:read",
            "ipd:discharge",
            "laboratory:read",
            "laboratory:create",
            "pharmacy:read",
            "reports:clinical",
        }
    ),
    "nurse": frozenset(
        {
            "patient:read",
            "patient:update",
            "opd:read",
            "opd:update",
            "ipd:read",
            "ipd:update",
        }
    ),
    "receptionist": frozenset(
        {
            "patient:read",
            "patient:create",
            "patient:update",
            "appointment:read",
            "appointment:create",
            "appointment:update",
            "appointment:delete",
            "opd:read",
            "opd:create",
            "opd:update",
            "opd:queue",
            "ipd:read",
            "ipd:admit",
            "billing:read",
            "billing:create",
            "billing:collect",
        }
    ),
    "pharmacist": frozenset(
        {
            "patient:read",
            "pharmacy:read",
            "pharmacy:create",
            "pharmacy:update",
            "pharmacy:dispense",
        }
    ),
    "lab_technician": frozenset(
        {
            "patient:read",
            "laboratory:read",
            "laboratory:update",
            "lab:verify",
            "lab:report",
        }
    ),
    "accountant": frozenset(
        {
            "patient:read",
            "ipd:read",
            "billing:read",
            "billing:create",
            "billing:update",
            "billing:void",
            "billing:collect",
            "reports:financial",
            "reports:export",
        }
    ),
}

# Roles cloned to hospital tenants (excludes platform_admin per R-03)
TENANT_ROLE_CODES: frozenset[str] = frozenset(
    code for code, _, _ in ROLE_CATALOG if code != "platform_admin"
)
