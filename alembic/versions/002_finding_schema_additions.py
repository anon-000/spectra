"""finding_schema_additions

Revision ID: 002
Revises: 001
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to findings table
    op.add_column("findings", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("findings", sa.Column("ai_verdict", sa.String(length=20), nullable=True))
    op.add_column("findings", sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("findings", sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("findings", sa.Column("pr_number", sa.Integer(), nullable=True))
    op.add_column("findings", sa.Column("commit_sha", sa.String(length=40), nullable=True))
    op.add_column("findings", sa.Column("cwe_id", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("findings", "cwe_id")
    op.drop_column("findings", "commit_sha")
    op.drop_column("findings", "pr_number")
    op.drop_column("findings", "last_seen")
    op.drop_column("findings", "first_seen")
    op.drop_column("findings", "ai_verdict")
    op.drop_column("findings", "confidence")
