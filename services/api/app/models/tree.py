"""Tree model — stub for Phase 1.

Schema details in docs/DATA_MODEL.md
TODO Phase 1:
- Spatial index on `location` (PostGIS GIST)
- FK to plots, owner, verified_by, job_id
- Auto-trigger to compute carbon_kg from biomass_kg
"""

from datetime import datetime
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class Tree(Base):
    __tablename__ = "trees"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Species
    species_name_th: Mapped[str | None] = mapped_column(String(100))
    species_name_sci: Mapped[str | None] = mapped_column(String(100), index=True)
    species_confidence: Mapped[float | None] = mapped_column(Float)

    # Location (PostGIS POINT, SRID 4326 = WGS84)
    location: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    # Measurements
    dbh_cm: Mapped[float] = mapped_column(Float, nullable=False)
    height_m: Mapped[float] = mapped_column(Float, nullable=False)

    # Computed
    volume_m3: Mapped[float | None] = mapped_column(Float)
    biomass_kg: Mapped[float | None] = mapped_column(Float)
    carbon_kg: Mapped[float | None] = mapped_column(Float)
    co2eq_kg: Mapped[float | None] = mapped_column(Float)

    # Source
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'lidar' | 'photogrammetry' | 'manual'

    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Tree {self.species_name_sci} DBH={self.dbh_cm}cm H={self.height_m}m>"
