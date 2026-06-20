"""Tenant settings data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.platform.tenant_setting import TenantSetting
from app.repositories.base import TenantScopedRepository


class SettingRepository(TenantScopedRepository):
    def list_all(self) -> list[TenantSetting]:
        stmt = self._base_query(TenantSetting).order_by(TenantSetting.setting_key)
        return list(self.db.scalars(stmt).all())

    def get_by_key(self, setting_key: str) -> TenantSetting | None:
        stmt = self._base_query(TenantSetting).where(TenantSetting.setting_key == setting_key)
        return self.db.scalars(stmt).first()

    def upsert(
        self,
        *,
        setting_key: str,
        setting_value: dict,
        description: str | None = None,
        created_by: uuid.UUID | None = None,
        updated_by: uuid.UUID | None = None,
    ) -> TenantSetting:
        existing = self.get_by_key(setting_key)
        if existing:
            existing.setting_value = setting_value
            if description is not None:
                existing.description = description
            existing.updated_by = updated_by
            self.db.add(existing)
            return existing

        row = TenantSetting(
            tenant_id=self.tenant_id,
            setting_key=setting_key,
            setting_value=setting_value,
            description=description,
            created_by=created_by,
        )
        self.db.add(row)
        return row

    def seed_defaults(self, defaults: dict[str, tuple[dict, str]], *, created_by: uuid.UUID | None = None) -> None:
        for key, (value, description) in defaults.items():
            if self.get_by_key(key) is None:
                self.upsert(
                    setting_key=key,
                    setting_value=value,
                    description=description,
                    created_by=created_by,
                )
