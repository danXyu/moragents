"""Models package."""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
metadata = Base.metadata

__all__ = ["Base", "metadata"]
