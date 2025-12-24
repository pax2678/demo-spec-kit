from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dashboard_user:dashboard_password@localhost/dashboard_db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Database dependency for FastAPI
def get_db():
    """FastAPI dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import all models to ensure they're registered with Base
from .user import User  # noqa: F401, E402
from .user_preferences import UserPreferences  # noqa: F401, E402
from .dashboard_widget import DashboardWidget  # noqa: F401, E402
from .metric_data import MetricData  # noqa: F401, E402