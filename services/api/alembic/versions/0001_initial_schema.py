"""initial schema — users, plots, trees, jobs, transactions, species_db

Revision ID: 0001
Revises:
Create Date: 2026-05-21

Creates the core schema for CarbonScan AI per docs/DATA_MODEL.md.
Requires PostGIS extension (enable separately via Supabase Dashboard or
scripts/setup_supabase.sql).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            server_default="community",
        ),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('community', 'industrial', 'auditor', 'admin')",
            name="users_role_check",
        ),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # --- species_db (reference table — seed via separate SQL) ---
    op.create_table(
        "species_db",
        sa.Column("name_sci", sa.String(100), primary_key=True),
        sa.Column("name_th", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=True),
        sa.Column("family", sa.String(100), nullable=True),
        sa.Column("wood_density", sa.Float(), nullable=False),
        sa.Column("wood_density_source", sa.String(255), nullable=True),
        sa.Column("agb_a", sa.Float(), nullable=True),
        sa.Column("agb_b", sa.Float(), nullable=True),
        sa.Column("agb_c", sa.Float(), nullable=True),
        sa.Column("agb_source", sa.String(255), nullable=True),
        sa.Column(
            "root_to_shoot_ratio",
            sa.Float(),
            nullable=False,
            server_default="0.24",
        ),
        sa.Column(
            "carbon_fraction",
            sa.Float(),
            nullable=False,
            server_default="0.47",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- plots ---
    op.create_table(
        "plots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "geometry",
            Geometry(geometry_type="POLYGON", srid=4326),
            nullable=False,
        ),
        sa.Column("province", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_plots_owner", "plots", ["owner_id"])
    # Note: GIST index on `geometry` column is auto-created by GeoAlchemy2
    # (Geometry column has spatial_index=True by default → idx_plots_geometry)
    op.create_index("idx_plots_province", "plots", ["province"])

    # --- jobs ---
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
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="queued",
        ),
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
        sa.CheckConstraint(
            "type IN ('las_upload', 'photogrammetry', 'pipeline')",
            name="jobs_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')",
            name="jobs_status_check",
        ),
        sa.CheckConstraint(
            "progress BETWEEN 0 AND 100",
            name="jobs_progress_check",
        ),
    )
    op.create_index("idx_jobs_user", "jobs", ["user_id"])
    op.create_index("idx_jobs_status", "jobs", ["status"])
    op.create_index("idx_jobs_created", "jobs", ["created_at"])

    # --- trees ---
    op.create_table(
        "trees",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "plot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("species_name_th", sa.String(100), nullable=True),
        sa.Column(
            "species_name_sci",
            sa.String(100),
            sa.ForeignKey("species_db.name_sci"),
            nullable=True,
        ),
        sa.Column("species_confidence", sa.Float(), nullable=True),
        sa.Column(
            "location",
            Geometry(geometry_type="POINT", srid=4326),
            nullable=False,
        ),
        sa.Column("elevation_m", sa.Float(), nullable=True),
        sa.Column("dbh_cm", sa.Float(), nullable=False),
        sa.Column("height_m", sa.Float(), nullable=False),
        sa.Column("crown_radius_m", sa.Float(), nullable=True),
        sa.Column("volume_m3", sa.Float(), nullable=True),
        sa.Column("biomass_kg", sa.Float(), nullable=True),
        sa.Column("carbon_kg", sa.Float(), nullable=True),
        sa.Column("co2eq_kg", sa.Float(), nullable=True),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("point_cloud_url", sa.Text(), nullable=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=True,
        ),
        sa.Column(
            "verified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_available",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "price_per_co2eq_kg",
            sa.Float(),
            server_default="2.0",
            nullable=False,
        ),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_type IN ('lidar', 'photogrammetry', 'manual')",
            name="trees_source_type_check",
        ),
    )
    op.create_index("idx_trees_plot", "trees", ["plot_id"])
    op.create_index("idx_trees_owner", "trees", ["owner_id"])
    op.create_index("idx_trees_species", "trees", ["species_name_sci"])
    # GIST on `location` is auto-created by GeoAlchemy2 → idx_trees_location
    # Partial index for marketplace queries — not auto-generated
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_trees_available ON trees(is_available) "
        "WHERE is_available = TRUE",
    )

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "buyer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "seller_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "tree_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trees.id"),
            nullable=False,
        ),
        sa.Column("co2eq_kg", sa.Float(), nullable=False),
        sa.Column("price_per_kg_thb", sa.Float(), nullable=False),
        sa.Column("payment_provider", sa.String(50), nullable=True),
        sa.Column(
            "payment_status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("payment_reference", sa.String(255), nullable=True),
        sa.Column("certificate_url", sa.Text(), nullable=True),
        sa.Column(
            "certificate_serial",
            sa.String(100),
            unique=True,
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "payment_status IN ('pending', 'completed', 'failed', 'refunded')",
            name="transactions_payment_status_check",
        ),
    )
    op.create_index("idx_tx_buyer", "transactions", ["buyer_id"])
    op.create_index("idx_tx_seller", "transactions", ["seller_id"])
    op.create_index("idx_tx_tree", "transactions", ["tree_id"])
    op.create_index("idx_tx_status", "transactions", ["payment_status"])

    # --- Triggers: auto-update updated_at ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
    )
    for table in ("users", "plots", "trees"):
        op.execute(
            f"""
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """,
        )


def downgrade() -> None:
    # Drop triggers + function
    for table in ("users", "plots", "trees"):
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse order (respecting FKs)
    op.drop_table("transactions")
    op.drop_table("trees")
    op.drop_table("jobs")
    op.drop_table("plots")
    op.drop_table("species_db")
    op.drop_table("users")
