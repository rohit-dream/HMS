"""User data access — tenant-scoped CRUD and search."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select

from app.core.constants import LOCKOUT_MINUTES, LOCKOUT_THRESHOLD
from app.models.core.user import User
from app.repositories.base import TenantScopedRepository


class UserRepository(TenantScopedRepository):
    def get_by_email(self, email: str) -> User | None:
        stmt = self._base_query(User).where(User.email == email.lower())
        return self.db.scalars(stmt).first()

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return super().get_by_id(User, user_id)

    def email_exists(self, email: str, *, exclude_user_id: uuid.UUID | None = None) -> bool:
        stmt = self._base_query(User).where(User.email == email.lower())
        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)
        return self.db.scalars(stmt).first() is not None

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        status: str = "active",
        phone: str | None = None,
        location_id: uuid.UUID | None = None,
        created_by: uuid.UUID | None = None,
    ) -> User:
        user = User(
            tenant_id=self.tenant_id,
            email=email.lower(),
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            location_id=location_id,
            status=status,
            created_by=created_by,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_fields(
        self,
        user: User,
        *,
        updated_by: uuid.UUID | None = None,
        **fields: object,
    ) -> User:
        for key, value in fields.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        user.updated_by = updated_by
        self.db.add(user)
        return user

    def disable(self, user: User, *, disabled_by: uuid.UUID | None = None) -> User:
        user.status = "inactive"
        user.updated_by = disabled_by
        self.db.add(user)
        return user

    def set_password(self, user: User, password_hash: str, *, updated_by: uuid.UUID | None = None) -> User:
        user.password_hash = password_hash
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.status == "locked":
            user.status = "active"
        user.updated_by = updated_by
        self.db.add(user)
        return user

    def search(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        stmt = self._base_query(User)
        count_stmt = select(func.count()).select_from(User).where(
            User.tenant_id == self.tenant_id,
            User.deleted_at.is_(None),
        )

        if status:
            stmt = stmt.where(User.status == status)
            count_stmt = count_stmt.where(User.status == status)

        if query:
            pattern = f"%{query.strip()}%"
            criterion = or_(
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
            )
            stmt = stmt.where(criterion)
            count_stmt = count_stmt.where(criterion)

        total = self.db.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        users = list(self.db.scalars(stmt).all())
        return users, int(total)

    def record_failed_login(self, user: User) -> User:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
            user.status = "locked"
            user.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_MINUTES)
        self.db.add(user)
        return user

    def record_successful_login(self, user: User) -> User:
        user.failed_login_attempts = 0
        user.status = "active"
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        self.db.add(user)
        return user

    def unlock_if_expired(self, user: User) -> User:
        if user.status == "locked" and user.locked_until:
            if datetime.now(UTC) >= user.locked_until:
                user.status = "active"
                user.locked_until = None
                user.failed_login_attempts = 0
                self.db.add(user)
        return user
