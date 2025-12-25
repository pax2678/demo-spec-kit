from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from . import Base


class UserRole(enum.Enum):
    """User roles with hierarchical permissions."""
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Primary key
    user_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="Unique user identifier"
    )
    
    # Basic user information
    username = Column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True,
        comment="Unique username for login"
    )
    
    email = Column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True,
        comment="User email address"
    )
    
    password_hash = Column(
        String(255), 
        nullable=False,
        comment="Hashed password for authentication"
    )
    
    # Role and status
    role = Column(
        Enum(UserRole), 
        nullable=False, 
        default=UserRole.VIEWER,
        comment="User role for authorization"
    )
    
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Whether user account is active"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Account creation timestamp"
    )
    
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last login timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Additional user information
    first_name = Column(
        String(100),
        nullable=True,
        comment="User first name"
    )
    
    last_name = Column(
        String(100),
        nullable=True,
        comment="User last name"
    )
    
    # Relationships
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        """String representation of User."""
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role.value}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_analyst(self) -> bool:
        """Check if user is an analyst or higher."""
        return self.role in [UserRole.ANALYST, UserRole.ADMIN]
    
    @property
    def is_viewer(self) -> bool:
        """Check if user is a viewer or higher."""
        return self.role in [UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN]
    
    def can_access_role(self, required_role: UserRole) -> bool:
        """Check if user can access resources requiring specific role."""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.ANALYST: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def to_dict(self) -> dict:
        """Convert user to dictionary for serialization."""
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }