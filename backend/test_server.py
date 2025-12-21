#!/usr/bin/env python3
"""
Minimal test server for dashboard frontend testing
Provides mock data without requiring database setup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import json

app = FastAPI(title="Dashboard Test API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_USER = {
    "user_id": "test-user-123",
    "username": "demo_admin", 
    "email": "admin@dashboard.com",
    "role": "admin",
    "is_active": True,
    "full_name": "Demo Administrator"
}

MOCK_WIDGETS = [
    {
        "widget_id": "widget-1",
        "widget_type": "chart",
        "title": "System Performance",
        "description": "CPU and Memory Usage",
        "metric_type": "system_performance",
        "metric_name": "cpu_usage",
        "configuration": {"chartType": "line", "timeRangeHours": 24},
        "position_x": 0,
        "position_y": 0,
        "width": 6,
        "height": 3,
        "is_active": True,
        "created_at": "2025-12-15T20:00:00Z",
        "updated_at": "2025-12-15T20:00:00Z"
    },
    {
        "widget_id": "widget-2", 
        "widget_type": "counter",
        "title": "Active Users",
        "description": "Currently logged in users",
        "metric_type": "user_activity",
        "metric_name": "active_users",
        "configuration": {"chartType": "stat"},
        "position_x": 6,
        "position_y": 0,
        "width": 6,
        "height": 3,
        "is_active": True,
        "created_at": "2025-12-15T20:00:00Z",
        "updated_at": "2025-12-15T20:00:00Z"
    },
    {
        "widget_id": "widget-3",
        "widget_type": "chart", 
        "title": "Error Rate",
        "description": "Application error percentage",
        "metric_type": "error_rate",
        "metric_name": "error_percentage",
        "configuration": {"chartType": "bar", "timeRangeHours": 12},
        "position_x": 0,
        "position_y": 3,
        "width": 12,
        "height": 4,
        "is_active": True,
        "created_at": "2025-12-15T20:00:00Z",
        "updated_at": "2025-12-15T20:00:00Z"
    }
]

def generate_mock_metrics(metric_name: str, hours: int = 24):
    """Generate mock time-series data"""
    data = []
    now = datetime.now()
    
    for i in range(hours * 4):  # 15-minute intervals
        timestamp = now - timedelta(minutes=15 * i)
        
        if metric_name == "cpu_usage":
            value = 45 + (i % 30) + (i % 7) * 2
        elif metric_name == "active_users":
            value = 150 + (i % 50)
        elif metric_name == "error_percentage":
            value = 2.5 + (i % 10) * 0.3
        else:
            value = 50 + (i % 20)
            
        data.append({
            "timestamp": timestamp.isoformat(),
            "value": round(value, 2),
            "unit": "%" if "percentage" in metric_name or "cpu" in metric_name else "count"
        })
    
    return sorted(data, key=lambda x: x["timestamp"])

@app.get("/")
async def root():
    return {"message": "Dashboard Test API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Auth endpoints
@app.post("/v1/auth/token")
async def login():
    return {
        "access_token": "mock-jwt-token-12345",
        "refresh_token": "mock-refresh-token-67890", 
        "token_type": "bearer",
        "expires_in": 3600
    }

@app.get("/v1/auth/me")
async def get_current_user():
    return MOCK_USER

@app.post("/v1/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

# Dashboard endpoints
@app.get("/v1/dashboard/widgets")
async def get_widgets():
    return MOCK_WIDGETS

@app.get("/v1/dashboard/metrics/latest")
async def get_latest_metrics():
    metrics = []
    for widget in MOCK_WIDGETS:
        metric_name = widget["metric_name"]
        latest_data = generate_mock_metrics(metric_name, 1)
        if latest_data:
            metrics.append({
                "metric_id": f"metric-{widget['widget_id']}",
                "metric_type": widget["metric_type"],
                "metric_name": metric_name,
                "value": latest_data[-1]["value"],
                "unit": latest_data[-1]["unit"],
                "timestamp": latest_data[-1]["timestamp"],
                "source_system": "test_system"
            })
    return metrics

@app.get("/v1/dashboard/metrics/{metric_name}/history")
async def get_metric_history(metric_name: str, hours: int = 24):
    return generate_mock_metrics(metric_name, hours)

if __name__ == "__main__":
    import uvicorn
    print("Starting Dashboard Test Server...")
    print("Backend API: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    try:
        uvicorn.run("test_server:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\nServer stopped!")