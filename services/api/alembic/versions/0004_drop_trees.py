"""drop trees and transactions

The `trees` table could not be filled. Tree.location is
Geometry(POINT, srid=4326) and NOT NULL — WGS84 latitude and longitude — and
nothing in this system produces a geographic coordinate. load_point_cloud reads
`las.x, las.y, las.z` and discards the CRS, so TreeResult.location is a mean
position in the point cloud's own frame. POST /trees was specified in the
module docstring and was never implementable as written.

Nothing read it either: GET /trees and GET /trees/{id} returned 501, the web
app never called them, and no code path anywhere constructed a Tree.

`transactions` goes with it. Its tree_id is a foreign key into trees, so it
cannot survive the drop unchanged, and a record of a carbon sale that cannot
say which tree was sold is not worth keeping. It has no ORM model and no code
touching it.

What is deliberately NOT dropped here, and why it is worth a look:

    users        no code reads or writes it. It was populated only by
                 DbJobStore.create, deleted with the async queue in 0003.
                 Authentication is Supabase's and lives in auth.users, a
                 different schema.
    plots        no ORM model, no code.
    species_db   no ORM model, no code. The species data actually used comes
                 from services/ml/data/species_db.csv, read by
                 app/services/species_catalogue.py.

With trees and transactions gone, no table in this database has a reader or a
writer. Dropping the rest — and with it DATABASE_URL, the async engine and
alembic — is a larger decision than this migration, so it is named rather than
taken.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-10
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # transactions first: its tree_id references trees.id.
    op.drop_index("idx_tx_tree", table_name="transactions")
    op.drop_index("idx_tx_seller", table_name="transactions")
    op.drop_index("idx_tx_buyer", table_name="transactions")
    op.drop_table("transactions")

    op.execute("DROP INDEX IF EXISTS idx_trees_available")
    op.drop_index("idx_trees_species", table_name="trees")
    op.drop_index("idx_trees_owner", table_name="trees")
    op.drop_index("idx_trees_plot", table_name="trees")
    op.drop_table("trees")


def downgrade() -> None:
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
        # job_id is NOT recreated: 0003 dropped the jobs table it referenced.
        sa.Column(
            "verified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_available", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "price_per_co2eq_kg", sa.Float(), server_default="2.0", nullable=False
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
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_trees_available ON trees(is_available) "
        "WHERE is_available = true"
    )

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
        sa.Column("certificate_serial", sa.String(100), unique=True, nullable=True),
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
