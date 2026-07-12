"""add jobs.result_json for full pipeline output

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("result_json", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "result_json")
