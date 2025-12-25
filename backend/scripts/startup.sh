#!/bin/bash
set -e

echo "🚀 Starting backend application..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 5

# Run database migrations (if any)
# alembic upgrade head

# Seed demo users
echo "🌱 Seeding demo users..."
python scripts/seed_demo_users.py || echo "⚠️  Demo user seeding failed (may already exist)"

# Start the application
echo "✅ Starting uvicorn..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
