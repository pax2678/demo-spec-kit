# Quickstart Guide: Dashboard Implementation

**Feature**: Operational Metrics Dashboard  
**Created**: 2025-12-15  
**Tech Stack**: React + FastAPI + PostgreSQL + Redis

## Overview

This guide provides the fastest path to implement a functional operational metrics dashboard with role-based authentication, real-time metrics display, and export capabilities.

## Prerequisites

- **Node.js 18+**: Frontend development and build tools
- **Python 3.11+**: Backend API development  
- **PostgreSQL 14+**: Database with TimescaleDB extension
- **Redis 6+**: Caching and session management
- **Docker**: Containerization for deployment

## Project Setup

### 1. Repository Structure

```bash
# Create main project directories
mkdir dashboard-app && cd dashboard-app
mkdir frontend backend
```

### 2. Frontend Setup (React + TypeScript)

```bash
cd frontend
npx create-react-app . --template typescript
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled
npm install chart.js react-chartjs-2 axios react-router-dom @types/react-router-dom
npm install @auth0/auth0-react  # For OAuth2 authentication

# Dev dependencies
npm install --save-dev @testing-library/jest-dom @playwright/test
```

### 3. Backend Setup (FastAPI + Python)

```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Core dependencies
pip install fastapi[all] uvicorn[standard] 
pip install sqlalchemy psycopg2-binary alembic
pip install python-jose[cryptography] passlib[bcrypt]
pip install redis pandas xlsxwriter

# Dev dependencies  
pip install pytest pytest-asyncio httpx
pip freeze > requirements.txt
```

### 4. Database Setup

```sql
-- PostgreSQL setup
CREATE DATABASE dashboard_db;
CREATE USER dashboard_user WITH PASSWORD 'dashboard_password';
GRANT ALL PRIVILEGES ON DATABASE dashboard_db TO dashboard_user;

-- Enable TimescaleDB extension
\c dashboard_db
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

### 5. Environment Configuration

Create `.env` files for configuration:

**Frontend (.env)**:
```bash
REACT_APP_API_URL=http://localhost:8000/v1
REACT_APP_AUTH0_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
REACT_APP_AUTH0_AUDIENCE=dashboard-api
```

**Backend (.env)**:
```bash
DATABASE_URL=postgresql://dashboard_user:dashboard_password@localhost/dashboard_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
```

## Core Implementation

### 1. Database Models (Backend)

Create `backend/src/models/database.py`:

```python
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    VIEWER = "viewer"
    ANALYST = "analyst" 
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    dashboard_layout = Column(JSON, default={})
    visible_widgets = Column(JSON, default=[])
    refresh_interval = Column(Integer, default=10)
    theme = Column(String(10), default="light")
    
    user = relationship("User", back_populates="preferences")
```

### 2. API Routes (Backend)

Create `backend/src/api/dashboard.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..models.database import User, MetricData
from ..auth.security import get_current_user
from ..database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics")
async def get_metrics(
    metric_type: Optional[str] = None,
    start_time: datetime = None,
    end_time: datetime = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch dashboard metrics with role-based filtering"""
    query = db.query(MetricData)
    
    if metric_type:
        query = query.filter(MetricData.metric_type == metric_type)
    if start_time:
        query = query.filter(MetricData.timestamp >= start_time)
    if end_time:
        query = query.filter(MetricData.timestamp <= end_time)
    
    # Role-based access control
    if current_user.role == UserRole.VIEWER:
        query = query.filter(MetricData.metric_type.in_(["user_activity"]))
    
    metrics = query.order_by(MetricData.timestamp.desc()).limit(1000).all()
    return metrics

@router.get("/widgets")
async def get_available_widgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get widgets available to user based on role"""
    query = db.query(DashboardWidget).filter(DashboardWidget.is_active == True)
    
    # Filter by minimum role requirement
    role_hierarchy = {"viewer": 1, "analyst": 2, "admin": 3}
    user_level = role_hierarchy[current_user.role.value]
    
    widgets = []
    for widget in query.all():
        widget_level = role_hierarchy[widget.min_role_required.value]
        if user_level >= widget_level:
            widgets.append(widget)
    
    return widgets
```

### 3. React Components (Frontend)

Create `frontend/src/components/Dashboard.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { Grid, Paper, Typography, Box } from '@mui/material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface MetricData {
  metric_id: string;
  metric_name: string;
  value: number;
  timestamp: string;
  unit: string;
}

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5 * 60 * 1000); // 5 minute refresh
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/v1/dashboard/metrics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = {
    labels: metrics.map(m => new Date(m.timestamp).toLocaleTimeString()),
    datasets: [{
      label: 'System Performance',
      data: metrics.map(m => m.value),
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      tension: 0.1
    }]
  };

  if (loading) return <Typography>Loading dashboard...</Typography>;

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Operational Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              System Performance Metrics
            </Typography>
            <Line data={chartData} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Stats
            </Typography>
            <Typography variant="body1">
              Active Users: {metrics.filter(m => m.metric_name === 'active_users').length}
            </Typography>
            <Typography variant="body1">
              Error Rate: {metrics.filter(m => m.metric_name === 'error_rate')[0]?.value || 0}%
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
```

## Development Commands

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start  # Runs on http://localhost:3000
```

### Testing

**Backend Tests**:
```bash
cd backend
pytest tests/ -v
```

**Frontend Tests**:
```bash
cd frontend
npm test  # Unit tests with Jest
npm run test:e2e  # E2E tests with Playwright
```

## Production Deployment

### Docker Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com/v1
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dashboard_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: timescale/timescaledb:latest-pg14
    environment:
      - POSTGRES_DB=dashboard_db
      - POSTGRES_USER=dashboard_user
      - POSTGRES_PASSWORD=dashboard_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Deployment Commands

```bash
# Build and deploy
docker-compose build
docker-compose up -d

# Check services
docker-compose ps
docker-compose logs -f backend
```

## Key Implementation Notes

1. **Authentication**: JWT-based with role hierarchy (viewer < analyst < admin)
2. **Performance**: Redis caching for 5-minute metric aggregation windows
3. **Real-time**: WebSocket connections for live metric updates
4. **Security**: Role-based API endpoint protection
5. **Scalability**: TimescaleDB for efficient time-series data storage
6. **Monitoring**: Built-in health checks and metric collection

## Next Steps

1. Configure OAuth2 provider (Auth0/Keycloak)
2. Implement widget drag-and-drop functionality
3. Add export functionality for Excel/CSV
4. Set up monitoring and alerting
5. Configure CI/CD pipeline
6. Add comprehensive error handling and logging

This quickstart provides a solid foundation for the operational dashboard with all core requirements implemented.