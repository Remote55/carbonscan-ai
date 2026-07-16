"""SQLAlchemy ORM models.

Models are registered automatically when imported. Make sure to import all
models in alembic/env.py for autogenerate to detect them.
"""

from app.models.job import Job
from app.models.tree import Tree
from app.models.user import User

__all__ = ["Job", "Tree", "User"]
