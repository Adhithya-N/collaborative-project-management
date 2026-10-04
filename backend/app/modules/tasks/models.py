"""Database model for tasks - the central unit of work users organize everything around."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """Fixed set of task board columns (customizable columns are a future extension)."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """A single unit of work belonging to one project."""

    __tablename__ = "tasks"
    __table_args__ = (
        # The task board's main query is "all tasks in project X with status Y" - this index speeds that up.
        Index("ix_tasks_project_id_status", "project_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        PgEnum(TaskStatus, name="task_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=TaskStatus.TODO,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        PgEnum(TaskPriority, name="task_priority", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=TaskPriority.MEDIUM,
    )
    # SET NULL (not CASCADE) - deleting a user should unassign their tasks, not delete the tasks.
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
