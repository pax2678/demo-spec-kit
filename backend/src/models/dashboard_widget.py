from sqlalchemy import Column, String, Integer, Boolean, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import uuid
import enum
from . import Base
from .user import UserRole


class WidgetType(enum.Enum):
    """Types of dashboard widgets."""
    CHART = "chart"
    GRAPH = "graph"
    COUNTER = "counter"
    TABLE = "table"


class DashboardWidget(Base):
    """Visual component definition for displaying specific metrics."""
    
    __tablename__ = "dashboard_widgets"
    
    # Primary key
    widget_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique widget identifier"
    )
    
    # Widget configuration
    widget_type = Column(
        Enum(WidgetType),
        nullable=False,
        comment="Type of widget (chart, graph, counter, table)"
    )
    
    title = Column(
        String(100),
        nullable=False,
        comment="Display title for the widget"
    )
    
    data_source = Column(
        String(100),
        nullable=False,
        comment="Metric type identifier this widget displays"
    )
    
    config = Column(
        JSON,
        nullable=True,
        comment="Widget-specific configuration (colors, axis, etc.)"
    )
    
    # Access control
    min_role_required = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.VIEWER,
        comment="Minimum role required to view this widget"
    )
    
    # Layout information
    position_x = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Grid X coordinate for default layout"
    )
    
    position_y = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Grid Y coordinate for default layout"
    )
    
    width = Column(
        Integer,
        nullable=False,
        default=4,
        comment="Widget width in grid units"
    )
    
    height = Column(
        Integer,
        nullable=False,
        default=3,
        comment="Widget height in grid units"
    )
    
    # Status and metadata
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether widget is available for use"
    )
    
    description = Column(
        String(500),
        nullable=True,
        comment="Description of what this widget displays"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When widget was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When widget was last updated"
    )
    
    def __repr__(self):
        """String representation of DashboardWidget."""
        return (f"<DashboardWidget(title='{self.title}', "
                f"type='{self.widget_type.value}', data_source='{self.data_source}')>")
    
    def to_dict(self) -> dict:
        """Convert widget to dictionary for serialization."""
        return {
            "widget_id": str(self.widget_id),
            "widget_type": self.widget_type.value,
            "title": self.title,
            "data_source": self.data_source,
            "config": self.config,
            "min_role_required": self.min_role_required.value,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "width": self.width,
            "height": self.height,
            "is_active": self.is_active,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def create_default_widgets(cls):
        """Create default dashboard widgets for initial setup."""
        default_widgets = [
            # System Performance Widgets
            {
                "widget_type": WidgetType.CHART,
                "title": "CPU Usage",
                "data_source": "system_performance",
                "description": "Real-time CPU utilization percentage",
                "position_x": 0,
                "position_y": 0,
                "width": 6,
                "height": 4,
                "min_role_required": UserRole.VIEWER,
                "config": {
                    "chart_type": "line",
                    "metric_name": "cpu_usage_percent",
                    "color": "#1976d2",
                    "show_legend": True,
                    "y_axis_max": 100
                }
            },
            {
                "widget_type": WidgetType.CHART,
                "title": "Memory Usage",
                "data_source": "system_performance",
                "description": "Memory utilization over time",
                "position_x": 6,
                "position_y": 0,
                "width": 6,
                "height": 4,
                "min_role_required": UserRole.VIEWER,
                "config": {
                    "chart_type": "area",
                    "metric_name": "memory_usage_percent",
                    "color": "#dc004e",
                    "show_legend": True,
                    "y_axis_max": 100
                }
            },
            
            # User Activity Widgets
            {
                "widget_type": WidgetType.COUNTER,
                "title": "Active Users",
                "data_source": "user_activity",
                "description": "Current number of active users",
                "position_x": 0,
                "position_y": 4,
                "width": 3,
                "height": 2,
                "min_role_required": UserRole.VIEWER,
                "config": {
                    "metric_name": "active_users",
                    "color": "#4caf50",
                    "show_trend": True,
                    "format": "number"
                }
            },
            {
                "widget_type": WidgetType.CHART,
                "title": "Page Views",
                "data_source": "user_activity",
                "description": "Page views per minute over time",
                "position_x": 3,
                "position_y": 4,
                "width": 9,
                "height": 3,
                "min_role_required": UserRole.VIEWER,
                "config": {
                    "chart_type": "bar",
                    "metric_name": "page_views",
                    "color": "#ff9800",
                    "show_legend": False
                }
            },
            
            # Error Rate Widgets
            {
                "widget_type": WidgetType.COUNTER,
                "title": "Error Rate",
                "data_source": "error_rate",
                "description": "Current HTTP error rate percentage",
                "position_x": 0,
                "position_y": 7,
                "width": 3,
                "height": 2,
                "min_role_required": UserRole.ANALYST,
                "config": {
                    "metric_name": "http_error_rate",
                    "color": "#f44336",
                    "threshold": 5,
                    "format": "percentage"
                }
            },
            {
                "widget_type": WidgetType.TABLE,
                "title": "System Health",
                "data_source": "system_performance",
                "description": "Overview of system health metrics",
                "position_x": 3,
                "position_y": 7,
                "width": 9,
                "height": 4,
                "min_role_required": UserRole.ANALYST,
                "config": {
                    "columns": ["metric_name", "value", "unit", "timestamp"],
                    "sort_by": "timestamp",
                    "sort_order": "desc",
                    "page_size": 10
                }
            }
        ]
        
        widgets = []
        for widget_data in default_widgets:
            widget = cls(**widget_data)
            widgets.append(widget)
        
        return widgets