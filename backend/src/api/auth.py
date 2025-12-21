from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
import uuid

from ..services.user_service import UserService
from ..models.user import User, UserRole
from ..config.settings import settings
from ..auth.middleware import get_database


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Create router
router = APIRouter()


# Request/Response models
class UserCreate(BaseModel):
    """User creation request model."""
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER


class UserResponse(BaseModel):
    """User response model."""
    user_id: str
    username: str
    email: str
    role: str
    is_active: bool
    full_name: str
    created_at: Optional[str]
    last_login: Optional[str]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Token refresh request model."""
    refresh_token: str


class PasswordChange(BaseModel):
    """Password change request model."""
    old_password: str
    new_password: str


class PasswordReset(BaseModel):
    """Password reset request model."""
    new_password: str


# Dependencies
def get_user_service(db: Session = Depends(get_database)) -> UserService:
    """Get user service instance."""
    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """Get current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = user_service.get_current_user(token)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control."""
    def check_role(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.can_access_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    
    return check_role


# Authentication endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user account."""
    try:
        user = user_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        return UserResponse(
            user_id=str(user.user_id),
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            full_name=user.full_name,
            created_at=user.created_at.isoformat() if user.created_at else None,
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """Authenticate user and return access/refresh tokens."""
    user = user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        data={"sub": user.username, "user_id": str(user.user_id), "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = user_service.create_refresh_token(
        data={"sub": user.username, "user_id": str(user.user_id)},
        expires_delta=refresh_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    user_service: UserService = Depends(get_user_service)
):
    """Refresh access token using refresh token."""
    payload = user_service.verify_token(token_data.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = user_service.get_user_by_username(username)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        data={"sub": user.username, "user_id": str(user.user_id), "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    # Create new refresh token
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = user_service.create_refresh_token(
        data={"sub": user.username, "user_id": str(user.user_id)},
        expires_delta=refresh_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse(
        user_id=str(current_user.user_id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        full_name=current_user.full_name,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Change current user's password."""
    success = user_service.change_password(
        current_user.user_id,
        password_data.old_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """Logout current user (client should discard tokens)."""
    return {"message": "Logged out successfully"}


# Admin-only endpoints
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service)
):
    """List users (admin only)."""
    users = user_service.get_users(
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active
    )
    
    return [
        UserResponse(
            user_id=str(user.user_id),
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            full_name=user.full_name,
            created_at=user.created_at.isoformat() if user.created_at else None,
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        for user in users
    ]


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service)
):
    """Activate user account (admin only)."""
    success = user_service.activate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User activated successfully"}


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service)
):
    """Deactivate user account (admin only)."""
    success = user_service.deactivate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: uuid.UUID,
    password_data: PasswordReset,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service)
):
    """Reset user password (admin only)."""
    success = user_service.reset_password(user_id, password_data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password reset successfully"}