from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from . import Base


class UserPreferences(Base):
    """User dashboard customization and preference settings."""
    
    __tablename__ = "user_preferences"
    
    # Primary key
    preference_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique preference identifier"
    )
    
    # User reference
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One preference record per user
        comment="Reference to user who owns these preferences"
    )
    
    # Dashboard layout and configuration
    dashboard_layout = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="Widget positions and sizes in grid layout"
    )
    
    visible_widgets = Column(
        JSON,
        nullable=True,
        default=list,
        comment="List of widget IDs that user wants to display"
    )
    
    default_filters = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="Default filter settings for dashboard"
    )
    
    # UI preferences
    theme = Column(
        String(10),
        nullable=False,
        default="light",
        comment="UI theme preference (light, dark)"
    )
    
    refresh_interval = Column(
        Integer,
        nullable=False,
        default=10,
        comment="Preferred refresh rate in minutes (5-15)"
    )
    
    # Additional preferences
    timezone = Column(
        String(50),
        nullable=True,
        default="UTC",
        comment="User's preferred timezone"
    )
    
    date_format = Column(
        String(20),
        nullable=False,
        default="YYYY-MM-DD",
        comment="Preferred date format"
    )
    
    # Notification preferences
    enable_notifications = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether to show dashboard notifications"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When preferences were created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When preferences were last updated"
    )
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        """String representation of UserPreferences."""
        return f"<UserPreferences(user_id='{self.user_id}', theme='{self.theme}')>"
    
    def to_dict(self) -> dict:
        """Convert preferences to dictionary."""
        return {
            "preference_id": str(self.preference_id),
            "user_id": str(self.user_id),
            "dashboard_layout": self.dashboard_layout,
            "visible_widgets": self.visible_widgets,
            "default_filters": self.default_filters,
            "theme": self.theme,
            "refresh_interval": self.refresh_interval,
            "timezone": self.timezone,
            "date_format": self.date_format,
            "enable_notifications": self.enable_notifications,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }