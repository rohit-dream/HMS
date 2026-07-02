"""platform.payment_methods data access."""

from __future__ import annotations

import uuid
from sqlalchemy import func, or_, select, update

from app.models.platform.payment_method import PaymentMethod
from app.repositories.base import TenantScopedRepository


class PaymentMethodRepository(TenantScopedRepository):
    def get_by_id(self, payment_method_id: uuid.UUID) -> PaymentMethod | None:
        return super().get_by_id(PaymentMethod, payment_method_id)

    def create(self, **kwargs: object) -> PaymentMethod:
        row = PaymentMethod(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(row)
        return row

    def get_default(self) -> PaymentMethod | None:
        stmt = self._base_query(PaymentMethod).where(PaymentMethod.is_default.is_(True)).order_by(
            PaymentMethod.created_at.desc()
        )
        return self.db.scalars(stmt).first()

    def unset_defaults(self, *, exclude_id: uuid.UUID | None = None) -> None:
        stmt = (
            update(PaymentMethod)
            .where(PaymentMethod.tenant_id == self.tenant_id)
            .where(PaymentMethod.deleted_at.is_(None))
            .where(PaymentMethod.is_default.is_(True))
        )
        if exclude_id is not None:
            stmt = stmt.where(PaymentMethod.id != exclude_id)
        self.db.execute(stmt)

    def count_active(self) -> int:
        stmt = select(func.count()).select_from(PaymentMethod).where(
            PaymentMethod.tenant_id == self.tenant_id,
            PaymentMethod.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0)

    def list(
        self,
        *,
        method_type: str | None = None,
        is_default: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PaymentMethod], int]:
        stmt = self._base_query(PaymentMethod)

        count_stmt = select(func.count()).select_from(PaymentMethod).where(
            PaymentMethod.tenant_id == self.tenant_id,
            PaymentMethod.deleted_at.is_(None),
        )

        if method_type is not None:
            stmt = stmt.where(PaymentMethod.method_type == method_type)
            count_stmt = count_stmt.where(PaymentMethod.method_type == method_type)

        if is_default is not None:
            stmt = stmt.where(PaymentMethod.is_default.is_(is_default))
            count_stmt = count_stmt.where(PaymentMethod.is_default.is_(is_default))

        if search:
            pattern = f"%{search.strip()}%"
            criterion = or_(
                PaymentMethod.gateway_customer_id.ilike(pattern),
                PaymentMethod.gateway_token_id.ilike(pattern),
                PaymentMethod.brand.ilike(pattern),
                PaymentMethod.last_four.ilike(pattern),
            )
            stmt = stmt.where(criterion)
            count_stmt = count_stmt.where(criterion)

        total = int(self.db.scalar(count_stmt) or 0)
        offset = (page - 1) * page_size
        stmt = stmt.order_by(PaymentMethod.created_at.desc()).offset(offset).limit(page_size)
        return list(self.db.scalars(stmt).all()), total

