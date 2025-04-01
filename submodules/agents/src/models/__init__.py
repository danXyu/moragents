"""Models package."""

from sqlalchemy.orm import declarative_base

from models.core.user_models import User, UserSetting

Base = declarative_base()
metadata = Base.metadata

__all__ = ["Base", "User", "UserSetting"]
