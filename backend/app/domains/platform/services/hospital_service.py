"""Hospital (tenant organization) profile, branches, and settings."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.setting_repository import SettingRepository
from app.domains.platform.repositories.tenant_repository import TenantRepository
from app.domains.platform.schemas.tenant import (
    HospitalProfileResponse,
    HospitalProfileUpdateRequest,
    LocationCreateRequest,
    LocationResponse,
    LocationUpdateRequest,
    SettingResponse,
    SettingUpsertRequest,
    SettingsBulkUpdateRequest,
)
from app.models.platform.tenant import Tenant


class HospitalService:
    """
    Tenant-scoped hospital management.

    Hospital = platform.tenants (organization) + tenant_locations (branches) + tenant_settings.
    All operations use JWT tenant_id — never client-supplied tenant identifiers.
    """

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._tenant_repo = TenantRepository(db)
        self._location_repo = LocationRepository(db, tenant_id)
        self._setting_repo = SettingRepository(db, tenant_id)

    def get_profile(self) -> HospitalProfileResponse:
        tenant = self._get_tenant()
        return HospitalProfileResponse.model_validate(tenant)

    def update_profile(
        self,
        payload: HospitalProfileUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> HospitalProfileResponse:
        tenant = self._get_tenant()
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")

        self._tenant_repo.update_profile(tenant, updated_by=actor_id, **update_data)
        self._mark_profile_complete_if_ready(tenant)
        self.db.commit()
        return HospitalProfileResponse.model_validate(tenant)

    def list_locations(self) -> list[LocationResponse]:
        locations = self._location_repo.list_active()
        return [LocationResponse.model_validate(loc) for loc in locations]

    def create_location(
        self,
        payload: LocationCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> LocationResponse:
        if self._location_repo.get_by_code(payload.code):
            raise ConflictError("Location code already exists", field="code")

        if payload.is_primary:
            self._location_repo.clear_primary_flags()

        location = self._location_repo.create(
            name=payload.name,
            code=payload.code,
            is_primary=payload.is_primary,
            address_line1=payload.address_line1,
            city=payload.city,
            state=payload.state,
            phone=payload.phone,
            is_active=True,
            created_by=actor_id,
        )
        self.db.commit()
        return LocationResponse.model_validate(location)

    def update_location(
        self,
        location_id: uuid.UUID,
        payload: LocationUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> LocationResponse:
        location = self._location_repo.get_by_id(location_id)
        if location is None:
            raise NotFoundError("Location not found", field="location_id")

        update_data = payload.model_dump(exclude_unset=True)
        if payload.is_primary is True:
            self._location_repo.clear_primary_flags(except_id=location.id)
            location.is_primary = True
            update_data.pop("is_primary", None)

        for key, value in update_data.items():
            setattr(location, key, value)
        location.updated_by = actor_id
        self.db.add(location)
        self.db.commit()
        return LocationResponse.model_validate(location)

    def list_settings(self) -> list[SettingResponse]:
        settings = self._setting_repo.list_all()
        return [SettingResponse.model_validate(s) for s in settings]

    def upsert_setting(
        self,
        setting_key: str,
        payload: SettingUpsertRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> SettingResponse:
        row = self._setting_repo.upsert(
            setting_key=setting_key,
            setting_value=payload.setting_value,
            description=payload.description,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.commit()
        return SettingResponse.model_validate(row)

    def bulk_update_settings(
        self,
        payload: SettingsBulkUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> list[SettingResponse]:
        results: list[SettingResponse] = []
        for key, value in payload.settings.items():
            row = self._setting_repo.upsert(
                setting_key=key,
                setting_value=value,
                created_by=actor_id,
                updated_by=actor_id,
            )
            results.append(SettingResponse.model_validate(row))
        self.db.commit()
        return results

    def _get_tenant(self) -> Tenant:
        tenant = self._tenant_repo.get_by_id(self.tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant not found", field="tenant_id")
        return tenant

    def _mark_profile_complete_if_ready(self, tenant: Tenant) -> None:
        """Update onboarding_progress when org profile has minimum fields."""
        if not (tenant.name and tenant.address_line1 and tenant.city):
            return
        progress = self._setting_repo.get_by_key("onboarding_progress")
        if progress is None:
            return
        value = dict(progress.setting_value)
        if not value.get("profile_complete"):
            value["profile_complete"] = True
            progress.setting_value = value
            self.db.add(progress)
