from datetime import timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .middleware import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    jwt_middleware,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


class OAuth2Service:
    """OAuth2 authentication service with JWT tokens."""
    
    def __init__(self):
        self.jwt_middleware = jwt_middleware
    
    async def authenticate_user(self, db: Session, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password."""
        # Import here to avoid circular imports
        from services.user_service import UserService
        
        user_service = UserService(db)
        user = await user_service.get_user_by_username(username)
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return {
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active
        }
    
    def create_token_response(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create token response with access and refresh tokens."""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token_data = {
            "sub": user_data["username"],
            "user_id": user_data["user_id"],
            "role": user_data["role"],
            "email": user_data["email"]
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user_data["username"], "user_id": user_data["user_id"]}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user_data["user_id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "role": user_data["role"]
            }
        }
    
    async def refresh_access_token(self, refresh_token: str, db: Session) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            payload = verify_refresh_token(refresh_token)
            username = payload.get("sub")
            user_id = payload.get("user_id")
            
            # Import here to avoid circular imports
            from services.user_service import UserService
            
            user_service = UserService(db)
            user = await user_service.get_user_by_username(username)
            
            if not user or str(user.user_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user"
                )
            
            # Create new tokens
            user_data = {
                "user_id": str(user.user_id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active
            }
            
            return self.create_token_response(user_data)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token"
            ) from e
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(jwt_middleware.security)):
        """Get current user from JWT token."""
        return await self.jwt_middleware.get_current_user(credentials)
    
    def require_role(self, required_role: str):
        """Require specific role for endpoint access."""
        return self.jwt_middleware.require_role(required_role)
    
    async def get_current_active_user(self, current_user: dict = Depends(get_current_user)):
        """Get current active user."""
        if not current_user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user


# Global service instance
oauth2_service = OAuth2Service()

# Dependency functions for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(jwt_middleware.security)):
    """FastAPI dependency to get current user."""
    return await oauth2_service.get_current_user(credentials)

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """FastAPI dependency to get current active user."""
    return await oauth2_service.get_current_active_user(current_user)

def require_admin_role():
    """FastAPI dependency to require admin role."""
    def admin_checker(user: dict = Depends(get_current_active_user)):
        return oauth2_service.require_role("admin")(user)
    return admin_checker

def require_analyst_role():
    """FastAPI dependency to require analyst role or higher."""
    def analyst_checker(user: dict = Depends(get_current_active_user)):
        return oauth2_service.require_role("analyst")(user)
    return analyst_checker

def require_viewer_role():
    """FastAPI dependency to require viewer role or higher."""
    def viewer_checker(user: dict = Depends(get_current_active_user)):
        return oauth2_service.require_role("viewer")(user)
    return viewer_checker