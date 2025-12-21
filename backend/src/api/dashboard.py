from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, timezone
import uuid

from ..services.metrics_service import MetricsService
from ..models.user import User, UserRole
from ..models.dashboard_widget import DashboardWidget
from ..auth.middleware import get_database
from .auth import get_current_active_user, require_role


# Create router
router = APIRouter()


# Request/Response models
class MetricDataResponse(BaseModel):
    """Single metric data point response."""
    metric_id: str
    metric_type: str
    metric_name: str
    value: float
    unit: Optional[str]
    timestamp: str
    source_system: Optional[str]
    metadata: Optional[Dict[str, Any]]


class MetricSummaryResponse(BaseModel):
    """Metric summary response."""
    metric_name: str
    current_value: float
    average: float
    minimum: float
    maximum: float
    count: int
    unit: Optional[str]
    last_updated: str
    trend: str


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response."""
    time_range: Dict[str, Any]
    metric_types: Dict[str, Dict[str, MetricSummaryResponse]]
    total_data_points: int


class MetricHistoryResponse(BaseModel):
    """Metric history response."""
    timestamp: str
    value: float
    unit: Optional[str]
    source: Optional[str]
    metadata: Optional[Dict[str, Any]]


class AggregatedMetricResponse(BaseModel):
    """Aggregated metric response."""
    timestamp: str
    value: float
    data_points: int
    aggregation: str
    interval: str


class AvailableMetricsResponse(BaseModel):
    """Available metrics response."""
    metric_types: Dict[str, List[str]]
    total_types: int
    total_metrics: int


class DashboardWidgetResponse(BaseModel):
    """Dashboard widget response."""
    widget_id: str
    widget_type: str
    title: str
    description: Optional[str]
    metric_type: str
    metric_name: str
    configuration: Dict[str, Any]
    position_x: int
    position_y: int
    width: int
    height: int
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class WidgetConfiguration(BaseModel):
    """Widget configuration request."""
    title: str
    description: Optional[str] = None
    metric_type: str
    metric_name: str
    widget_type: str = "chart"
    configuration: Dict[str, Any] = {}
    position_x: int = 0
    position_y: int = 0
    width: int = 4
    height: int = 3


# Dependencies
def get_metrics_service(db: Session = Depends(get_database)) -> MetricsService:
    """Get metrics service instance."""
    return MetricsService(db)


# Dashboard metrics endpoints
@router.get("/metrics/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get comprehensive dashboard metrics summary."""
    summary_data = metrics_service.get_dashboard_metrics_summary(hours)
    
    # Convert to response format
    metric_types = {}
    for metric_type, metrics in summary_data["metric_types"].items():
        metric_types[metric_type] = {
            metric_name: MetricSummaryResponse(**metric_data)
            for metric_name, metric_data in metrics.items()
        }
    
    return DashboardSummaryResponse(
        time_range=summary_data["time_range"],
        metric_types=metric_types,
        total_data_points=summary_data["total_data_points"]
    )


@router.get("/metrics/latest", response_model=List[MetricDataResponse])
async def get_latest_metrics(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of metrics"),
    metric_types: Optional[str] = Query(None, description="Comma-separated metric types"),
    metric_names: Optional[str] = Query(None, description="Comma-separated metric names"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get latest metric data points with optional filtering."""
    type_filter = metric_types.split(",") if metric_types else None
    name_filter = metric_names.split(",") if metric_names else None
    
    metrics = metrics_service.get_latest_metrics(
        metric_types=type_filter,
        metric_names=name_filter,
        limit=limit
    )
    
    return [
        MetricDataResponse(
            metric_id=str(metric.metric_id),
            metric_type=metric.metric_type,
            metric_name=metric.metric_name,
            value=float(metric.value),
            unit=metric.unit,
            timestamp=metric.timestamp.isoformat(),
            source_system=metric.source_system,
            metadata=metric.metadata
        )
        for metric in metrics
    ]


@router.get("/metrics/{metric_name}/history", response_model=List[MetricHistoryResponse])
async def get_metric_history(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    max_points: int = Query(100, ge=10, le=1000, description="Maximum data points"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get time-series history for a specific metric."""
    history = metrics_service.get_metric_history(metric_name, hours, max_points)
    
    return [
        MetricHistoryResponse(
            timestamp=point["timestamp"],
            value=point["value"],
            unit=point["unit"],
            source=point["source"],
            metadata=point["metadata"]
        )
        for point in history
    ]


@router.get("/metrics/{metric_name}/aggregated", response_model=List[AggregatedMetricResponse])
async def get_aggregated_metrics(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    interval: str = Query("1h", regex="^(5m|15m|1h|1d)$", description="Aggregation interval"),
    function: str = Query("avg", regex="^(avg|sum|min|max|count)$", description="Aggregation function"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get aggregated metrics over time intervals."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    aggregated_data = metrics_service.get_aggregated_metrics(
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        aggregation_interval=interval,
        aggregation_function=function
    )
    
    return [
        AggregatedMetricResponse(
            timestamp=point["timestamp"],
            value=point["value"],
            data_points=point["data_points"],
            aggregation=point["aggregation"],
            interval=point["interval"]
        )
        for point in aggregated_data
    ]


@router.get("/metrics/{metric_name}/statistics")
async def get_metric_statistics(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get statistical analysis for a specific metric."""
    stats = metrics_service.get_metric_statistics(metric_name, hours)
    
    if stats.get("no_data"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for metric '{metric_name}' in the last {hours} hours"
        )
    
    return stats


@router.get("/metrics/types/{metric_type}", response_model=List[MetricDataResponse])
async def get_metrics_by_type(
    metric_type: str,
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of metrics"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get metrics filtered by type."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    metrics = metrics_service.get_metrics_by_type(
        metric_type=metric_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return [
        MetricDataResponse(
            metric_id=str(metric.metric_id),
            metric_type=metric.metric_type,
            metric_name=metric.metric_name,
            value=float(metric.value),
            unit=metric.unit,
            timestamp=metric.timestamp.isoformat(),
            source_system=metric.source_system,
            metadata=metric.metadata
        )
        for metric in metrics
    ]


# Widget availability endpoints
@router.get("/widgets/available", response_model=AvailableMetricsResponse)
async def get_available_metrics(
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get all available metrics for dashboard widgets."""
    available_metrics = metrics_service.get_available_metrics()
    
    total_metrics = sum(len(names) for names in available_metrics.values())
    
    return AvailableMetricsResponse(
        metric_types=available_metrics,
        total_types=len(available_metrics),
        total_metrics=total_metrics
    )


@router.get("/widgets", response_model=List[DashboardWidgetResponse])
async def get_dashboard_widgets(
    is_active: bool = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Get dashboard widgets configuration."""
    query = db.query(DashboardWidget)
    
    if is_active is not None:
        query = query.filter(DashboardWidget.is_active == is_active)
    
    widgets = query.order_by(DashboardWidget.position_y, DashboardWidget.position_x).all()
    
    return [
        DashboardWidgetResponse(
            widget_id=str(widget.widget_id),
            widget_type=widget.widget_type,
            title=widget.title,
            description=widget.description,
            metric_type=widget.metric_type,
            metric_name=widget.metric_name,
            configuration=widget.configuration,
            position_x=widget.position_x,
            position_y=widget.position_y,
            width=widget.width,
            height=widget.height,
            is_active=widget.is_active,
            created_at=widget.created_at.isoformat() if widget.created_at else "",
            updated_at=widget.updated_at.isoformat() if widget.updated_at else ""
        )
        for widget in widgets
    ]


@router.post("/widgets", response_model=DashboardWidgetResponse)
async def create_dashboard_widget(
    widget_config: WidgetConfiguration,
    current_user: User = Depends(require_role(UserRole.ANALYST)),
    db: Session = Depends(get_database)
):
    """Create a new dashboard widget (analyst+ only)."""
    widget = DashboardWidget(
        widget_type=widget_config.widget_type,
        title=widget_config.title,
        description=widget_config.description,
        metric_type=widget_config.metric_type,
        metric_name=widget_config.metric_name,
        configuration=widget_config.configuration,
        position_x=widget_config.position_x,
        position_y=widget_config.position_y,
        width=widget_config.width,
        height=widget_config.height,
        is_active=True
    )
    
    db.add(widget)
    db.commit()
    db.refresh(widget)
    
    return DashboardWidgetResponse(
        widget_id=str(widget.widget_id),
        widget_type=widget.widget_type,
        title=widget.title,
        description=widget.description,
        metric_type=widget.metric_type,
        metric_name=widget.metric_name,
        configuration=widget.configuration,
        position_x=widget.position_x,
        position_y=widget.position_y,
        width=widget.width,
        height=widget.height,
        is_active=widget.is_active,
        created_at=widget.created_at.isoformat() if widget.created_at else "",
        updated_at=widget.updated_at.isoformat() if widget.updated_at else ""
    )


@router.put("/widgets/{widget_id}", response_model=DashboardWidgetResponse)
async def update_dashboard_widget(
    widget_id: uuid.UUID,
    widget_config: WidgetConfiguration,
    current_user: User = Depends(require_role(UserRole.ANALYST)),
    db: Session = Depends(get_database)
):
    """Update dashboard widget configuration (analyst+ only)."""
    widget = db.query(DashboardWidget).filter(
        DashboardWidget.widget_id == widget_id
    ).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Update widget fields
    widget.widget_type = widget_config.widget_type
    widget.title = widget_config.title
    widget.description = widget_config.description
    widget.metric_type = widget_config.metric_type
    widget.metric_name = widget_config.metric_name
    widget.configuration = widget_config.configuration
    widget.position_x = widget_config.position_x
    widget.position_y = widget_config.position_y
    widget.width = widget_config.width
    widget.height = widget_config.height
    
    db.commit()
    db.refresh(widget)
    
    return DashboardWidgetResponse(
        widget_id=str(widget.widget_id),
        widget_type=widget.widget_type,
        title=widget.title,
        description=widget.description,
        metric_type=widget.metric_type,
        metric_name=widget.metric_name,
        configuration=widget.configuration,
        position_x=widget.position_x,
        position_y=widget.position_y,
        width=widget.width,
        height=widget.height,
        is_active=widget.is_active,
        created_at=widget.created_at.isoformat() if widget.created_at else "",
        updated_at=widget.updated_at.isoformat() if widget.updated_at else ""
    )


@router.delete("/widgets/{widget_id}")
async def delete_dashboard_widget(
    widget_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.ANALYST)),
    db: Session = Depends(get_database)
):
    """Delete dashboard widget (analyst+ only)."""
    widget = db.query(DashboardWidget).filter(
        DashboardWidget.widget_id == widget_id
    ).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    db.delete(widget)
    db.commit()
    
    return {"message": "Widget deleted successfully"}


# Development/testing endpoints
@router.post("/metrics/populate-sample-data")
async def populate_sample_data(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Populate database with sample metrics data for development (admin only)."""
    result = metrics_service.populate_sample_data()
    
    return {
        "message": "Sample data populated successfully",
        "details": result
    }


@router.delete("/metrics/cleanup")
async def cleanup_old_metrics(
    retention_days: int = Query(90, ge=1, le=365, description="Retention period in days"),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Clean up old metric data (admin only)."""
    deleted_count = metrics_service.cleanup_old_metrics(retention_days)
    
    return {
        "message": f"Cleaned up {deleted_count} old metric records",
        "retention_days": retention_days
    }