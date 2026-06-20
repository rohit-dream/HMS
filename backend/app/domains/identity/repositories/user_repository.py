"""User data access for authentication."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.core.constants import LOCKOUT_MINUTES, LOCKOUT_THRESHOLD
from app.models.core.user import User
from app.repositories.base import TenantScopedRepository


class UserRepository(TenantScopedRepository):
    def get_by_email(self, email: str) -> User | None:
        stmt = self._base_query(User).where(User.email == email.lower())
        return self.db.scalars(stmt).first()

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return super().get_by_id(User, user_id)

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
