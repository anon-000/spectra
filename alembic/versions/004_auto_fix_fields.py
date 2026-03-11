"""auto_fix_fields

Revision ID: 004
Revises: 003
Create Date: 2026-03-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("auto_fix_status", sa.String(20), nullable=True))
    op.add_column("findings", sa.Column("auto_fix_pr_url", sa.String(1024), nullable=True))
    op.add_column("findings", sa.Column("auto_fix_pr_number", sa.Integer(), nullable=True))
    op.add_column("findings", sa.Column("auto_fix_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("findings", "auto_fix_error")
    op.drop_column("findings", "auto_fix_pr_number")
    op.drop_column("findings", "auto_fix_pr_url")
    op.drop_column("findings", "auto_fix_status")
