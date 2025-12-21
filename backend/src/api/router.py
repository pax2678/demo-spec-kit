from fastapi import APIRouter
from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .user_preferences import router as preferences_router
from .export import router as export_router

# Create main API router
api_router = APIRouter()

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint for container health monitoring."""
    return {
        "status": "healthy",
        "service": "dashboard-api",
        "version": "1.0.0"
    }

# Include sub-routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    dashboard_router,
    prefix="/dashboard",
    tags=["dashboard"]
)

api_router.include_router(
    preferences_router,
    prefix="/users",
    tags=["user-management"]
)

api_router.include_router(
    export_router,
    prefix="/export",
    tags=["export"]
)