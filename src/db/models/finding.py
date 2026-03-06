from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Finding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "findings"

    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.id"))
    scan: Mapped["Scan"] = relationship(back_populates="findings")

    repo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repos.id"), index=True
    )

    # Tool info
    tool: Mapped[str] = mapped_column(String(50))  # semgrep, trufflehog, osv-scanner, etc.
    rule_id: Mapped[str] = mapped_column(String(512))

    # Location
    file_path: Mapped[str] = mapped_column(String(1024))
    line_start: Mapped[int | None] = mapped_column(Integer)
    line_end: Mapped[int | None] = mapped_column(Integer)
    snippet: Mapped[str | None] = mapped_column(Text)

    # Classification
    severity: Mapped[str] = mapped_column(String(20), index=True)  # critical, high, medium, low
    category: Mapped[str] = mapped_column(String(50))  # sast, sca, secret, license
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)

    # Dedup
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)

    # AI triage
    ai_severity: Mapped[str | None] = mapped_column(String(20))
    ai_explanation: Mapped[str | None] = mapped_column(Text)
    ai_suggested_fix: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    ai_verdict: Mapped[str | None] = mapped_column(String(20))  # true_positive, false_positive, needs_review

    # Status: open, resolved, suppressed, false_positive
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)

    # Dedup timelines
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Source context
    pr_number: Mapped[int | None] = mapped_column(Integer)
    commit_sha: Mapped[str | None] = mapped_column(String(40))

    # SCA-specific
    package_name: Mapped[str | None] = mapped_column(String(512))
    package_version: Mapped[str | None] = mapped_column(String(100))
    cve_id: Mapped[str | None] = mapped_column(String(20))
    cwe_id: Mapped[str | None] = mapped_column(String(20))

    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    events: Mapped[list["FindingEvent"]] = relationship(back_populates="finding")
