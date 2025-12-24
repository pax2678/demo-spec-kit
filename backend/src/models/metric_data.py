from sqlalchemy import Column, String, Numeric, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from . import Base


class MetricData(Base):
    """Time-series operational data points for dashboard display."""
    
    __tablename__ = "metric_data"
    
    # Primary key
    metric_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique metric data point identifier"
    )
    
    # Metric classification
    metric_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Category of metric (system_performance, user_activity, error_rate)"
    )
    
    metric_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Specific metric identifier"
    )
    
    # Metric value and measurement
    value = Column(
        Numeric(precision=20, scale=6),
        nullable=False,
        comment="Measured metric value"
    )
    
    unit = Column(
        String(20),
        nullable=True,
        comment="Unit of measurement (requests/sec, percentage, count, etc.)"
    )
    
    # Time information
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Timestamp when metric was recorded"
    )
    
    # Source and context
    source_system = Column(
        String(100),
        nullable=True,
        comment="Origin system that generated the metric"
    )

    metric_metadata = Column(
        JSON,
        nullable=True,
        comment="Additional context data for the metric"
    )
    
    # Timestamps for data management
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this record was created"
    )
    
    # Indexes for efficient querying
    __table_args__ = (
        # Composite index for time-series queries
        Index('idx_metric_type_timestamp', 'metric_type', 'timestamp'),
        Index('idx_metric_name_timestamp', 'metric_name', 'timestamp'),
        Index('idx_source_timestamp', 'source_system', 'timestamp'),
        # Time-based partitioning index
        Index('idx_timestamp_metric_type', 'timestamp', 'metric_type'),
    )
    
    def __repr__(self):
        """String representation of MetricData."""
        return (f"<MetricData(metric_name='{self.metric_name}', "
                f"value={self.value}, timestamp='{self.timestamp}')>")
    
    @property
    def metric_key(self) -> str:
        """Generate a unique key for this metric type and name."""
        return f"{self.metric_type}:{self.metric_name}"
    
    def to_dict(self) -> dict:
        """Convert metric data to dictionary for serialization."""
        return {
            "metric_id": str(self.metric_id),
            "metric_type": self.metric_type,
            "metric_name": self.metric_name,
            "value": float(self.value) if self.value is not None else None,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_system": self.source_system,
            "metadata": self.metric_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def create_sample_data(cls):
        """Create sample metric data for testing and development."""
        import random
        from datetime import datetime, timedelta
        
        sample_metrics = [
            # System Performance Metrics
            {
                "metric_type": "system_performance",
                "metric_name": "cpu_usage_percent",
                "unit": "percentage",
                "source_system": "server-01"
            },
            {
                "metric_type": "system_performance", 
                "metric_name": "memory_usage_percent",
                "unit": "percentage",
                "source_system": "server-01"
            },
            {
                "metric_type": "system_performance",
                "metric_name": "disk_io_operations",
                "unit": "operations/sec",
                "source_system": "server-01"
            },
            {
                "metric_type": "system_performance",
                "metric_name": "network_throughput",
                "unit": "mbps",
                "source_system": "server-01"
            },
            
            # User Activity Metrics
            {
                "metric_type": "user_activity",
                "metric_name": "active_users",
                "unit": "count",
                "source_system": "web-app"
            },
            {
                "metric_type": "user_activity",
                "metric_name": "page_views",
                "unit": "count/min",
                "source_system": "web-app"
            },
            {
                "metric_type": "user_activity",
                "metric_name": "session_duration",
                "unit": "minutes",
                "source_system": "web-app"
            },
            
            # Error Rate Metrics
            {
                "metric_type": "error_rate",
                "metric_name": "http_error_rate",
                "unit": "percentage",
                "source_system": "api-gateway"
            },
            {
                "metric_type": "error_rate",
                "metric_name": "database_errors",
                "unit": "count/min",
                "source_system": "database"
            },
            {
                "metric_type": "error_rate",
                "metric_name": "application_exceptions",
                "unit": "count/min",
                "source_system": "backend"
            }
        ]
        
        # Generate data points for last 24 hours
        now = datetime.utcnow()
        sample_data = []
        
        for metric in sample_metrics:
            for hours_ago in range(24):
                timestamp = now - timedelta(hours=hours_ago)
                
                # Generate realistic values based on metric type
                if "percentage" in metric.get("unit", ""):
                    value = random.uniform(5, 95)
                elif "count" in metric.get("unit", ""):
                    value = random.randint(10, 1000)
                elif "operations" in metric.get("unit", ""):
                    value = random.randint(100, 5000)
                elif "mbps" in metric.get("unit", ""):
                    value = random.uniform(10, 100)
                elif "minutes" in metric.get("unit", ""):
                    value = random.uniform(1, 30)
                else:
                    value = random.uniform(0, 100)
                
                sample_data.append(cls(
                    metric_type=metric["metric_type"],
                    metric_name=metric["metric_name"],
                    value=value,
                    unit=metric["unit"],
                    timestamp=timestamp,
                    source_system=metric["source_system"],
                    metric_metadata={"generated": True, "sample_data": True}
                ))
        
        return sample_data