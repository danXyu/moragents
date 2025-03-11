from datetime import datetime
from typing import List

from sqlalchemy import JSON, DateTime, String, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base
from models.service.user_service_models import UserModel, UserSettingModel


class User(Base):
    """SQLAlchemy model for users"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    settings: Mapped[List["UserSetting"]] = relationship(
        "UserSetting", back_populates="user", cascade="all, delete-orphan"
    )

    def to_service_model(self) -> UserModel:
        """Convert to service model"""
        return UserModel(
            id=self.id, wallet_address=self.wallet_address, created_at=self.created_at, updated_at=self.updated_at
        )

    @classmethod
    def from_service_model(cls, model: UserModel) -> "User":
        """Create from service model"""
        return cls(
            id=model.id, wallet_address=model.wallet_address, created_at=model.created_at, updated_at=model.updated_at
        )


class UserSetting(Base):
    """SQLAlchemy model for user settings"""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    settings_key: Mapped[str] = mapped_column(String(255), nullable=False)
    settings_value: Mapped[JSON] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="settings")

    __table_args__ = (
        # Ensure unique key per user
        {"unique_constraints": [("user_id", "settings_key")]}
    )

    def to_service_model(self) -> UserSettingModel:
        """Convert to service model"""
        return UserSettingModel(
            id=self.id,
            user_id=self.user_id,
            settings_key=self.settings_key,
            settings_value=self.settings_value,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_service_model(cls, model: UserSettingModel) -> "UserSetting":
        """Create from service model"""
        return cls(
            id=model.id,
            user_id=model.user_id,
            settings_key=model.settings_key,
            settings_value=model.settings_value,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
