"""analytics_indexes

Revision ID: 005
Revises: 004
Create Date: 2026-03-06

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_findings_repo_id_created_at",
        "findings",
        ["repo_id", "created_at"],
    )
    op.create_index(
        "ix_finding_events_action_created_at",
        "finding_events",
        ["action", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_finding_events_action_created_at", table_name="finding_events")
    op.drop_index("ix_findings_repo_id_created_at", table_name="findings")
