#!/usr/bin/env python3
"""
Seed script to create demo users for the dashboard application.
Run this after database initialization to populate demo accounts.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Import Base first
from src.models import Base
# Import all models to register them with Base.metadata
from src.models.user import User, UserRole
from src.models.user_preferences import UserPreferences
from src.models.dashboard_widget import DashboardWidget
from src.models.metric_data import MetricData

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dashboard_user:dashboard_password@db:5432/dashboard_db"
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_demo_users():
    """Create demo users with predefined credentials."""
    print("🔧 Connecting to database...")
    engine = create_engine(DATABASE_URL)

    # Create all tables if they don't exist
    print("📋 Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Demo users to create
        demo_users = [
            {
                "username": "demo_viewer",
                "email": "viewer@demo.local",
                "password": "demo123",
                "role": UserRole.VIEWER,
                "first_name": "Demo",
                "last_name": "Viewer",
            },
            {
                "username": "demo_analyst",
                "email": "analyst@demo.local",
                "password": "demo123",
                "role": UserRole.ANALYST,
                "first_name": "Demo",
                "last_name": "Analyst",
            },
            {
                "username": "demo_admin",
                "email": "admin@demo.local",
                "password": "demo123",
                "role": UserRole.ADMIN,
                "first_name": "Demo",
                "last_name": "Admin",
            },
        ]

        created_count = 0
        skipped_count = 0

        for user_data in demo_users:
            # Check if user already exists
            existing_user = db.query(User).filter(
                User.username == user_data["username"]
            ).first()

            if existing_user:
                print(f"⏭️  User '{user_data['username']}' already exists, skipping...")
                skipped_count += 1
                continue

            # Create new user with hashed password
            hashed_password = pwd_context.hash(user_data["password"])

            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hashed_password,
                role=user_data["role"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                is_active=True,
            )

            db.add(new_user)
            created_count += 1
            print(f"✅ Created user: {user_data['username']} ({user_data['role'].value})")

        # Commit all changes
        db.commit()

        print(f"\n🎉 Demo user creation complete!")
        print(f"   Created: {created_count} users")
        print(f"   Skipped: {skipped_count} users (already exist)")

        if created_count > 0:
            print(f"\n📝 Demo Credentials:")
            print(f"   Viewer:  demo_viewer  / demo123")
            print(f"   Analyst: demo_analyst / demo123")
            print(f"   Admin:   demo_admin   / demo123")

    except Exception as e:
        print(f"❌ Error creating demo users: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Starting demo user seed script...")
    create_demo_users()
