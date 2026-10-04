"""Database model for notifications - user-facing alerts, distinct from the activity log.

Unlike ActivityLog (permanent, append-only audit trail), a Notification is mutable (is_read
flips) and user-scoped (only the recipient ever sees it) - different lifecycle, different table.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Notification(Base):
    """One alert delivered to one user - e.g. 'you were assigned a task'."""

    __tablename__ = "notifications"
    __table_args__ = (
        # The main query is "this user's unread notifications" - this index speeds that up.
        Index("ix_notifications_user_id_is_read", "user_id", "is_read"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Flexible JSON payload - shape depends on `type` (e.g. {"task_id": "...", "task_title": "..."}).
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
