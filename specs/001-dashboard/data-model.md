# Data Model: Dashboard

**Created**: 2025-12-15  
**Source**: Extracted from feature specification entities

## Core Entities

### User
Represents authenticated users with role-based access to dashboard metrics.

**Fields**:
- `user_id` (UUID, Primary Key): Unique identifier
- `username` (String, Unique): Login credential
- `email` (String, Unique): Contact and identity verification
- `role` (Enum): Access level - `admin`, `viewer`, `analyst`
- `created_at` (Timestamp): Account creation time
- `last_login` (Timestamp): Last authentication time
- `is_active` (Boolean): Account status

**Validation Rules**:
- Email must be valid format and unique
- Role must be one of defined enum values
- Username must be alphanumeric, 3-50 characters

**Relationships**:
- One-to-One with UserPreferences
- One-to-Many with DashboardSession

### UserPreferences
Stores saved dashboard configuration and personalization settings.

**Fields**:
- `preference_id` (UUID, Primary Key): Unique identifier
- `user_id` (UUID, Foreign Key): Owner reference
- `dashboard_layout` (JSON): Widget positions and sizes
- `visible_widgets` (JSON Array): List of enabled widget IDs
- `default_filters` (JSON): Default filter settings
- `theme` (String): UI theme preference - `light`, `dark`
- `refresh_interval` (Integer): Preferred refresh rate in minutes (5-15)
- `updated_at` (Timestamp): Last modification time

**Validation Rules**:
- refresh_interval must be between 5 and 15 minutes
- dashboard_layout must be valid JSON structure
- visible_widgets must contain valid widget references

**State Transitions**:
- Created on first user login with default settings
- Updated when user modifies layout or preferences
- Persists across all user sessions

### DashboardWidget
Visual component definition for displaying specific metrics.

**Fields**:
- `widget_id` (UUID, Primary Key): Unique identifier
- `widget_type` (Enum): Display format - `chart`, `graph`, `counter`, `table`
- `title` (String): Display name for widget
- `data_source` (String): Metric type identifier
- `config` (JSON): Widget-specific configuration (colors, axis, etc.)
- `min_role_required` (Enum): Minimum access level - `viewer`, `analyst`, `admin`
- `position_x` (Integer): Grid X coordinate (default layout)
- `position_y` (Integer): Grid Y coordinate (default layout)
- `width` (Integer): Widget width in grid units
- `height` (Integer): Widget height in grid units
- `is_active` (Boolean): Widget availability status

**Validation Rules**:
- title must be 1-100 characters
- position and size values must be non-negative
- config must be valid JSON
- data_source must reference available metric

### MetricData
Time-series operational data points for dashboard display.

**Fields**:
- `metric_id` (UUID, Primary Key): Unique identifier
- `metric_type` (String): Category - `system_performance`, `user_activity`, `error_rate`
- `metric_name` (String): Specific metric identifier
- `value` (Decimal): Measured value
- `timestamp` (Timestamp): Data point time
- `source_system` (String): Origin system identifier
- `metadata` (JSON): Additional context data
- `unit` (String): Measurement unit (requests/sec, percentage, count)

**Validation Rules**:
- timestamp must not be future date
- value must be non-negative for count metrics
- metric_type must be one of defined operational categories
- metadata must be valid JSON if provided

**Relationships**:
- Partitioned by timestamp (TimescaleDB hypertable)
- Indexed on metric_type and timestamp for query performance

### FilterConfiguration
User-applied constraints for data display customization.

**Fields**:
- `filter_id` (UUID, Primary Key): Unique identifier
- `user_id` (UUID, Foreign Key): Owner reference
- `filter_name` (String): User-defined name
- `date_range_start` (Timestamp): Start time for data window
- `date_range_end` (Timestamp): End time for data window
- `metric_categories` (JSON Array): Selected metric types
- `source_systems` (JSON Array): Selected source systems
- `is_active` (Boolean): Currently applied status
- `created_at` (Timestamp): Filter creation time

**Validation Rules**:
- date_range_start must be before date_range_end
- date range cannot exceed 90 days
- metric_categories must contain valid metric types
- filter_name must be unique per user

**State Transitions**:
- Created when user applies custom filters
- Activated/deactivated based on user selection
- Persists until user removes or modifies

### DashboardSession
Tracks active user sessions for performance monitoring and analytics.

**Fields**:
- `session_id` (UUID, Primary Key): Unique identifier
- `user_id` (UUID, Foreign Key): User reference
- `start_time` (Timestamp): Session beginning
- `end_time` (Timestamp): Session conclusion
- `last_activity` (Timestamp): Most recent interaction
- `widgets_viewed` (JSON Array): Accessed widget IDs
- `filters_applied` (Integer): Number of filter operations
- `export_requests` (Integer): Number of data exports

**Validation Rules**:
- end_time must be after start_time if provided
- last_activity must be within session timespan
- Count fields must be non-negative

## Database Schema Design

### PostgreSQL with TimescaleDB Extension

**TimescaleDB Hypertables**:
- `metric_data` - Partitioned by timestamp for time-series optimization
- Continuous aggregates for 5-minute, hourly, and daily rollups
- Data retention policy: 90 days detailed, 1 year aggregated

**Standard Tables**:
- `users` - User account information
- `user_preferences` - Dashboard customization data
- `dashboard_widgets` - Widget definitions and metadata
- `filter_configurations` - Saved filter settings
- `dashboard_sessions` - User activity tracking

**Indexes**:
- `metric_data`: (timestamp, metric_type), (metric_name, timestamp)
- `users`: (email), (username)
- `user_preferences`: (user_id)
- `dashboard_widgets`: (widget_type), (min_role_required)

## Redis Caching Strategy

**Cache Keys**:
- `dashboard:metrics:{metric_type}:{timeframe}` - Aggregated metric data (TTL: 5 minutes)
- `user:preferences:{user_id}` - User dashboard settings (TTL: 1 hour)
- `session:{session_id}` - Active session data (TTL: 24 hours)
- `widget:config:{widget_id}` - Widget configuration (TTL: 1 hour)

**Cache Invalidation**:
- Metrics cache: Auto-expire every 5 minutes aligned with refresh interval
- User preferences: Invalidate on user settings update
- Session cache: Sliding expiration on user activity