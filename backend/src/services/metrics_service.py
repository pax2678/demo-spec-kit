from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json

from ..models.metric_data import MetricData
from ..models.dashboard_widget import DashboardWidget
from ..config.settings import settings


class MetricsService:
    """Service for metrics data aggregation and dashboard display."""
    
    def __init__(self, db: Session):
        """Initialize metrics service with database session."""
        self.db = db
    
    def get_metrics_by_type(
        self,
        metric_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MetricData]:
        """Get metrics filtered by type and time range."""
        query = self.db.query(MetricData).filter(
            MetricData.metric_type == metric_type
        )
        
        if start_time:
            query = query.filter(MetricData.timestamp >= start_time)
        
        if end_time:
            query = query.filter(MetricData.timestamp <= end_time)
        
        query = query.order_by(desc(MetricData.timestamp))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_metrics_by_name(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MetricData]:
        """Get metrics filtered by name and time range."""
        query = self.db.query(MetricData).filter(
            MetricData.metric_name == metric_name
        )
        
        if start_time:
            query = query.filter(MetricData.timestamp >= start_time)
        
        if end_time:
            query = query.filter(MetricData.timestamp <= end_time)
        
        query = query.order_by(desc(MetricData.timestamp))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_latest_metrics(
        self,
        metric_types: Optional[List[str]] = None,
        metric_names: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[MetricData]:
        """Get the most recent metrics with optional filtering."""
        query = self.db.query(MetricData)
        
        if metric_types:
            query = query.filter(MetricData.metric_type.in_(metric_types))
        
        if metric_names:
            query = query.filter(MetricData.metric_name.in_(metric_names))
        
        return query.order_by(desc(MetricData.timestamp)).limit(limit).all()
    
    def get_aggregated_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        aggregation_interval: str = "1h",  # 5m, 15m, 1h, 1d
        aggregation_function: str = "avg"  # avg, sum, min, max, count
    ) -> List[Dict[str, Any]]:
        """Get aggregated metrics over time intervals."""
        # Convert aggregation interval to minutes
        interval_minutes = {
            "5m": 5,
            "15m": 15,
            "1h": 60,
            "1d": 1440
        }.get(aggregation_interval, 60)
        
        # Choose aggregation function
        func_map = {
            "avg": func.avg,
            "sum": func.sum,
            "min": func.min,
            "max": func.max,
            "count": func.count
        }
        agg_func = func_map.get(aggregation_function, func.avg)
        
        # Build query with time-based grouping
        query = self.db.query(
            func.date_trunc(
                'hour' if interval_minutes >= 60 else 'minute',
                MetricData.timestamp
            ).label('time_bucket'),
            agg_func(MetricData.value).label('aggregated_value'),
            func.count(MetricData.metric_id).label('data_points')
        ).filter(
            and_(
                MetricData.metric_name == metric_name,
                MetricData.timestamp >= start_time,
                MetricData.timestamp <= end_time
            )
        ).group_by('time_bucket').order_by('time_bucket')
        
        results = query.all()
        
        return [
            {
                "timestamp": result.time_bucket.isoformat(),
                "value": float(result.aggregated_value) if result.aggregated_value else 0,
                "data_points": result.data_points,
                "aggregation": aggregation_function,
                "interval": aggregation_interval
            }
            for result in results
        ]
    
    def get_dashboard_metrics_summary(
        self,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """Get comprehensive metrics summary for dashboard display."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # Get all unique metric types and names
        metric_types_query = self.db.query(MetricData.metric_type).distinct()
        metric_types = [mt[0] for mt in metric_types_query.all()]
        
        summary = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": time_range_hours
            },
            "metric_types": {},
            "total_data_points": 0
        }
        
        for metric_type in metric_types:
            # Get metrics for this type
            metrics = self.get_metrics_by_type(
                metric_type, start_time, end_time
            )
            
            # Group by metric name
            metrics_by_name = {}
            for metric in metrics:
                if metric.metric_name not in metrics_by_name:
                    metrics_by_name[metric.metric_name] = []
                metrics_by_name[metric.metric_name].append(metric)
            
            # Calculate statistics for each metric
            metric_stats = {}
            for metric_name, metric_list in metrics_by_name.items():
                values = [float(m.value) for m in metric_list]
                if values:
                    metric_stats[metric_name] = {
                        "current_value": values[0],  # Most recent
                        "average": sum(values) / len(values),
                        "minimum": min(values),
                        "maximum": max(values),
                        "count": len(values),
                        "unit": metric_list[0].unit,
                        "last_updated": metric_list[0].timestamp.isoformat(),
                        "trend": self._calculate_trend(values)
                    }
            
            summary["metric_types"][metric_type] = metric_stats
            summary["total_data_points"] += len(metrics)
        
        return summary
    
    def get_metric_history(
        self,
        metric_name: str,
        hours: int = 24,
        max_points: int = 100
    ) -> List[Dict[str, Any]]:
        """Get time-series data for a specific metric."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        metrics = self.get_metrics_by_name(
            metric_name, start_time, end_time, max_points
        )
        
        return [
            {
                "timestamp": metric.timestamp.isoformat(),
                "value": float(metric.value),
                "unit": metric.unit,
                "source": metric.source_system,
                "metadata": metric.metadata
            }
            for metric in reversed(metrics)  # Chronological order
        ]
    
    def create_metric_data_point(
        self,
        metric_type: str,
        metric_name: str,
        value: float,
        unit: Optional[str] = None,
        source_system: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> MetricData:
        """Create a new metric data point."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        metric = MetricData(
            metric_type=metric_type,
            metric_name=metric_name,
            value=Decimal(str(value)),
            unit=unit,
            timestamp=timestamp,
            source_system=source_system,
            metadata=metadata
        )
        
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        
        return metric
    
    def bulk_create_metrics(
        self,
        metrics_data: List[Dict[str, Any]]
    ) -> List[MetricData]:
        """Create multiple metric data points efficiently."""
        metrics = []
        
        for data in metrics_data:
            metric = MetricData(
                metric_type=data["metric_type"],
                metric_name=data["metric_name"],
                value=Decimal(str(data["value"])),
                unit=data.get("unit"),
                timestamp=data.get("timestamp", datetime.now(timezone.utc)),
                source_system=data.get("source_system"),
                metadata=data.get("metadata")
            )
            metrics.append(metric)
        
        self.db.add_all(metrics)
        self.db.commit()
        
        return metrics
    
    def get_available_metrics(self) -> Dict[str, List[str]]:
        """Get all available metric types and their metric names."""
        query = self.db.query(
            MetricData.metric_type,
            MetricData.metric_name
        ).distinct()
        
        results = query.all()
        
        available_metrics = {}
        for metric_type, metric_name in results:
            if metric_type not in available_metrics:
                available_metrics[metric_type] = []
            if metric_name not in available_metrics[metric_type]:
                available_metrics[metric_type].append(metric_name)
        
        return available_metrics
    
    def cleanup_old_metrics(self, retention_days: Optional[int] = None) -> int:
        """Remove old metric data beyond retention period."""
        if retention_days is None:
            retention_days = settings.METRICS_RETENTION_DAYS
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        deleted_count = self.db.query(MetricData).filter(
            MetricData.timestamp < cutoff_date
        ).count()
        
        self.db.query(MetricData).filter(
            MetricData.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        
        return deleted_count
    
    def get_metric_statistics(
        self,
        metric_name: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get statistical analysis for a specific metric."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        metrics = self.get_metrics_by_name(metric_name, start_time, end_time)
        
        if not metrics:
            return {
                "metric_name": metric_name,
                "no_data": True
            }
        
        values = [float(m.value) for m in metrics]
        
        # Calculate percentiles
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        def percentile(p):
            index = int(p * n / 100)
            return sorted_values[min(index, n-1)]
        
        return {
            "metric_name": metric_name,
            "time_range_hours": hours,
            "count": len(values),
            "current": values[0],  # Most recent
            "average": sum(values) / len(values),
            "minimum": min(values),
            "maximum": max(values),
            "median": percentile(50),
            "p90": percentile(90),
            "p95": percentile(95),
            "p99": percentile(99),
            "standard_deviation": self._calculate_std_dev(values),
            "trend": self._calculate_trend(values),
            "unit": metrics[0].unit,
            "last_updated": metrics[0].timestamp.isoformat()
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values (most recent first)."""
        if len(values) < 2:
            return "stable"
        
        # Compare recent vs older values
        recent_avg = sum(values[:len(values)//3]) / (len(values)//3)
        older_avg = sum(values[len(values)//3:]) / (len(values) - len(values)//3)
        
        change_percent = ((recent_avg - older_avg) / older_avg) * 100
        
        if change_percent > 5:
            return "increasing"
        elif change_percent < -5:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        return variance ** 0.5
    
    def populate_sample_data(self) -> Dict[str, int]:
        """Populate database with sample metrics data for development."""
        sample_data = MetricData.create_sample_data()
        
        # Clear existing sample data
        self.db.query(MetricData).filter(
            MetricData.metadata.contains({"sample_data": True})
        ).delete(synchronize_session=False)
        
        # Add new sample data
        self.db.add_all(sample_data)
        self.db.commit()
        
        return {
            "created_metrics": len(sample_data),
            "metric_types": len(set(m.metric_type for m in sample_data)),
            "time_range_hours": 24
        }