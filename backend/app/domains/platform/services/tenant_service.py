"""Tenant provisioning and lifecycle management."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.email import EmailNotificationService
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.config import get_settings
from app.core.database import set_rls_tenant_context
from app.core.security import hash_password
from app.domains.identity.services.rbac_service import RbacProvisioner
from app.domains.platform.constants import (
    ACTIVATABLE_STATUSES,
    CURRENT_PRIVACY_POLICY_VERSION,
    CURRENT_TERMS_VERSION,
    DEFAULT_TENANT_SETTINGS,
    LEGAL_ACCEPTANCE_SETTING_KEY,
    PRIMARY_LOCATION_CODE,
    PRIMARY_LOCATION_NAME,
    SUSPENDABLE_STATUSES,
)
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.setting_repository import SettingRepository
from app.domains.platform.repositories.tenant_repository import TenantRepository
from app.domains.platform.schemas.tenant import (
    TenantCreateRequest,
    TenantRegisterRequest,
    TenantRegisterResponse,
    TenantResponse,
)
from app.models.core.user import User
from app.models.platform.tenant import Tenant


class TenantService:
    """Platform tenant provisioning, activation, and suspension."""

    TRIAL_DAYS = 14

    def __init__(self, db: Session) -> None:
        self.db = db
        self._tenant_repo = TenantRepository(db)

    def register_tenant(self, payload: TenantRegisterRequest) -> TenantRegisterResponse:
        """Full self-service registration with owner user."""
        tenant_id = self._provision_core(payload)
        owner_user_id = self._create_owner_user(
            tenant_id=tenant_id,
            email=str(payload.email).lower(),
            first_name=payload.owner_first_name,
            last_name=payload.owner_last_name,
            password=payload.owner_password,
        )
        self._record_legal_acceptance(tenant_id, payload, owner_user_id)
        self.db.commit()
        tenant = self._tenant_repo.get_by_id(tenant_id)
        assert tenant is not None
        EmailNotificationService(get_settings()).send_welcome(
            to_email=str(payload.email).lower(),
            tenant_slug=tenant.slug,
            hospital_name=tenant.name,
        )
        return TenantRegisterResponse(
            tenant=TenantResponse.model_validate(tenant),
            trial_ends_at=datetime.now(UTC) + timedelta(days=self.TRIAL_DAYS),
        )

    def create_tenant(self, payload: TenantCreateRequest) -> TenantResponse:
        """Platform-admin tenant creation without owner user."""
        tenant_id = self._provision_core(payload)
        self.db.commit()
        tenant = self._tenant_repo.get_by_id(tenant_id)
        assert tenant is not None
        return TenantResponse.model_validate(tenant)

    def activate_tenant(self, tenant_id: uuid.UUID, *, actor_id: uuid.UUID | None = None) -> TenantResponse:
        tenant = self._get_tenant_or_404(tenant_id)
        if tenant.status not in ACTIVATABLE_STATUSES:
            raise ValidationError(
                f"Cannot activate tenant in status '{tenant.status}'",
                field="status",
            )
        self._tenant_repo.update_status(tenant, "active", updated_by=actor_id)
        self.db.commit()
        return TenantResponse.model_validate(tenant)

    def suspend_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
        reason: str | None = None,
    ) -> TenantResponse:
        tenant = self._get_tenant_or_404(tenant_id)
        if tenant.status not in SUSPENDABLE_STATUSES:
            raise ValidationError(
                f"Cannot suspend tenant in status '{tenant.status}'",
                field="status",
            )
        if reason:
            metadata = dict(tenant.metadata_ or {})
            metadata["suspension_reason"] = reason
            metadata["suspended_at"] = datetime.now(UTC).isoformat()
            tenant.metadata_ = metadata
        self._tenant_repo.update_status(tenant, "suspended", updated_by=actor_id)
        self.db.commit()
        return TenantResponse.model_validate(tenant)

    def get_tenant(self, tenant_id: uuid.UUID) -> TenantResponse:
        tenant = self._get_tenant_or_404(tenant_id)
        return TenantResponse.model_validate(tenant)

    def _provision_core(self, payload: TenantCreateRequest | TenantRegisterRequest) -> uuid.UUID:
        subdomain = payload.subdomain or payload.slug
        if self._tenant_repo.slug_exists(payload.slug):
            raise ConflictError("Tenant slug already exists", field="slug")
        if self._tenant_repo.subdomain_exists(subdomain):
            raise ConflictError("Tenant subdomain already exists", field="subdomain")

        try:
            tenant_id = self._tenant_repo.create_via_db_function(
                name=payload.name,
                slug=payload.slug,
                email=str(payload.email).lower(),
                subdomain=subdomain,
                country=payload.country,
                timezone=payload.timezone,
                currency=payload.currency,
            )
        except IntegrityError as exc:
            raise ConflictError("Tenant could not be created — duplicate identifier", field="slug") from exc

        set_rls_tenant_context(self.db, tenant_id)
        self._provision_hospital_resources(tenant_id)
        return tenant_id

    def _provision_hospital_resources(self, tenant_id: uuid.UUID) -> None:
        """RBAC, primary location, and default settings per MULTI_TENANT_DESIGN §3."""
        provisioner = RbacProvisioner(self.db)
        provisioner.seed_system_rbac()
        provisioner.provision_tenant_rbac(tenant_id)

        location_repo = LocationRepository(self.db, tenant_id)
        location_repo.create(
            name=PRIMARY_LOCATION_NAME,
            code=PRIMARY_LOCATION_CODE,
            is_primary=True,
            is_active=True,
        )

        setting_repo = SettingRepository(self.db, tenant_id)
        setting_repo.seed_defaults(DEFAULT_TENANT_SETTINGS)

    def _create_owner_user(
        self,
        *,
        tenant_id: uuid.UUID,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> uuid.UUID:
        user = User(
            tenant_id=tenant_id,
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            status="active",
        )
        self.db.add(user)
        self.db.flush()
        RbacProvisioner(self.db).assign_role(tenant_id, user.id, "hospital_owner")
        return user.id

    def _record_legal_acceptance(
        self,
        tenant_id: uuid.UUID,
        payload: TenantRegisterRequest,
        accepted_by_user_id: uuid.UUID,
    ) -> None:
        """Persist versioned Terms + Privacy acceptance at signup (NFR-COMP-008)."""
        setting_repo = SettingRepository(self.db, tenant_id)
        setting_repo.upsert(
            setting_key=LEGAL_ACCEPTANCE_SETTING_KEY,
            setting_value={
                "terms_version": CURRENT_TERMS_VERSION,
                "privacy_policy_version": CURRENT_PRIVACY_POLICY_VERSION,
                "terms_accepted": payload.accept_terms,
                "privacy_policy_accepted": payload.accept_privacy_policy,
                "accepted_at": datetime.now(UTC).isoformat(),
                "accepted_by_user_id": str(accepted_by_user_id),
                "accepted_by_email": str(payload.email).lower(),
            },
            description="Signup legal acceptance audit record",
            created_by=accepted_by_user_id,
            updated_by=accepted_by_user_id,
        )

    def _get_tenant_or_404(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = self._tenant_repo.get_by_id(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant not found", field="tenant_id")
        return tenant
