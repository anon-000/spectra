from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Scan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scans"

    repo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repos.id"))
    repo: Mapped["Repo"] = relationship(back_populates="scans")

    # PR context
    pr_number: Mapped[int | None] = mapped_column(Integer)
    commit_sha: Mapped[str] = mapped_column(String(40))
    branch: Mapped[str | None] = mapped_column(String(255))
    trigger: Mapped[str] = mapped_column(String(50))  # "pull_request", "push", "manual"

    # Status: pending, running, completed, failed
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    check_run_id: Mapped[int | None] = mapped_column(BigInteger)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Counters
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)

    findings: Mapped[list["Finding"]] = relationship(back_populates="scan")
