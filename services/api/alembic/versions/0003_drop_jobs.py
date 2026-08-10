"""drop the async job queue

The `jobs` table backed an async pipeline queue that nothing used. No web
client called POST /jobs/analyze, no deployment started the worker that was
supposed to drain it, and the endpoint answered 202 "queued" for work that
could not run. Analysis is synchronous and finishes inside a request: the
pipeline measured a 16-tree plot of 447,089 points in 10 seconds and the
service caps an analysis at 200,000 points.

trees.job_id went with it — it pointed only at this table.

The downgrade recreates both, matching 0001 plus the result_json column 0002
added, so the pair round-trips. If an async queue is ever wanted again it
should be designed against a real requirement, and the storage question
settled first: uploads landed on container-local disk, which cannot be shared
between an API and a worker in separate containers.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-10
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dropped first: its foreign key is the only thing keeping jobs referenced.
    op.drop_column("trees", "job_id")
    op.drop_index("idx_jobs_created", table_name="jobs")
    op.drop_index("idx_jobs_status", table_name="jobs")
    op.drop_index("idx_jobs_user", table_name="jobs")
    op.drop_table("jobs")


def downgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "plot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plots.id"),
            nullable=True,
        ),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("input_url", sa.Text(), nullable=False),
        sa.Column("output_url", sa.Text(), nullable=True),
        sa.Column("progress", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_stage", sa.String(100), nullable=True),
        sa.Column("total_trees_detected", sa.Integer(), nullable=True),
        sa.Column("total_carbon_kg", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_traceback", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.String(255), nullable=True),
        sa.Column("gpu_seconds_used", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Added by 0002; recreated here so downgrading to 0002 lands on the
        # schema 0002 actually described.
        sa.Column("result_json", postgresql.JSONB(), nullable=True),
        sa.CheckConstraint(
            "type IN ('las_upload', 'photogrammetry', 'pipeline')",
            name="jobs_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')",
            name="jobs_status_check",
        ),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="jobs_progress_check"),
    )
    op.create_index("idx_jobs_user", "jobs", ["user_id"])
    op.create_index("idx_jobs_status", "jobs", ["status"])
    op.create_index("idx_jobs_created", "jobs", ["created_at"])
    op.add_column(
        "trees",
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=True,
        ),
    )
