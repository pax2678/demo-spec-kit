from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import uuid

from ..models.user import User, UserRole
from ..config.settings import settings


class UserService:
    """Service for user authentication and management operations."""
    
    def __init__(self, db: Session):
        """Initialize user service with database session."""
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate hash for a password."""
        return self.pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        
        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def create_user(
        self, 
        username: str, 
        email: str, 
        password: str,
        role: UserRole = UserRole.VIEWER,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Create a new user."""
        # Check if username or email already exists
        if self.get_user_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        
        if self.get_user_by_email(email):
            raise ValueError(f"Email '{email}' already exists")
        
        # Create new user
        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(
        self,
        user_id: uuid.UUID,
        **kwargs
    ) -> Optional[User]:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Handle password separately
        if 'password' in kwargs:
            kwargs['password_hash'] = self.get_password_hash(kwargs.pop('password'))
        
        # Update allowed fields
        allowed_fields = {
            'username', 'email', 'password_hash', 'role', 
            'first_name', 'last_name', 'is_active'
        }
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def deactivate_user(self, user_id: uuid.UUID) -> bool:
        """Deactivate a user account."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        
        return True
    
    def activate_user(self, user_id: uuid.UUID) -> bool:
        """Activate a user account."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        self.db.commit()
        
        return True
    
    def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get list of users with optional filtering."""
        query = self.db.query(User)
        
        if role is not None:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token."""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = self.get_user_by_username(username)
        if user is None or not user.is_active:
            return None
        
        return user
    
    def check_role_permission(
        self, 
        user: User, 
        required_role: UserRole
    ) -> bool:
        """Check if user has required role permissions."""
        if not user or not user.is_active:
            return False
        
        return user.can_access_role(required_role)
    
    def change_password(
        self, 
        user_id: uuid.UUID, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """Change user password."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify old password
        if not self.verify_password(old_password, user.password_hash):
            return False
        
        # Update password
        user.password_hash = self.get_password_hash(new_password)
        self.db.commit()
        
        return True
    
    def reset_password(self, user_id: uuid.UUID, new_password: str) -> bool:
        """Reset user password (admin operation)."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.password_hash = self.get_password_hash(new_password)
        self.db.commit()
        
        return True