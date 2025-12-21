import axios, { AxiosResponse } from 'axios';
import authService from './authService';

// API base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

// Configure axios instance for dashboard API
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authentication header to all requests
api.interceptors.request.use(
  (config) => {
    const token = authService.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Types for dashboard data
export interface MetricData {
  metric_id: string;
  metric_type: string;
  metric_name: string;
  value: number;
  unit?: string;
  timestamp: string;
  source_system?: string;
  metadata?: Record<string, any>;
}

export interface MetricSummary {
  metric_name: string;
  current_value: number;
  average: number;
  minimum: number;
  maximum: number;
  count: number;
  unit?: string;
  last_updated: string;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface DashboardSummary {
  time_range: {
    start: string;
    end: string;
    hours: number;
  };
  metric_types: Record<string, Record<string, MetricSummary>>;
  total_data_points: number;
}

export interface MetricHistory {
  timestamp: string;
  value: number;
  unit?: string;
  source?: string;
  metadata?: Record<string, any>;
}

export interface AggregatedMetric {
  timestamp: string;
  value: number;
  data_points: number;
  aggregation: string;
  interval: string;
}

export interface MetricStatistics {
  metric_name: string;
  time_range_hours: number;
  count: number;
  current: number;
  average: number;
  minimum: number;
  maximum: number;
  median: number;
  p90: number;
  p95: number;
  p99: number;
  standard_deviation: number;
  trend: string;
  unit?: string;
  last_updated: string;
}

export interface AvailableMetrics {
  metric_types: Record<string, string[]>;
  total_types: number;
  total_metrics: number;
}

export interface DashboardWidget {
  widget_id: string;
  widget_type: string;
  title: string;
  description?: string;
  metric_type: string;
  metric_name: string;
  configuration: Record<string, any>;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WidgetConfiguration {
  title: string;
  description?: string;
  metric_type: string;
  metric_name: string;
  widget_type?: string;
  configuration?: Record<string, any>;
  position_x?: number;
  position_y?: number;
  width?: number;
  height?: number;
}

export interface DashboardRefreshConfig {
  intervalMinutes: number;
  autoRefresh: boolean;
}

class DashboardService {
  private refreshIntervalId: NodeJS.Timeout | null = null;
  private refreshConfig: DashboardRefreshConfig = {
    intervalMinutes: 5,
    autoRefresh: false,
  };

  /**
   * Get dashboard summary with overview of all metrics
   */
  async getDashboardSummary(hours: number = 24): Promise<DashboardSummary> {
    try {
      const response: AxiosResponse<DashboardSummary> = await api.get(
        `/dashboard/metrics/summary?hours=${hours}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get dashboard summary:', error);
      throw new Error('Failed to load dashboard summary');
    }
  }

  /**
   * Get latest metric data points
   */
  async getLatestMetrics(
    limit: number = 50,
    metricTypes?: string[],
    metricNames?: string[]
  ): Promise<MetricData[]> {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      
      if (metricTypes?.length) {
        params.append('metric_types', metricTypes.join(','));
      }
      
      if (metricNames?.length) {
        params.append('metric_names', metricNames.join(','));
      }

      const response: AxiosResponse<MetricData[]> = await api.get(
        `/dashboard/metrics/latest?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get latest metrics:', error);
      throw new Error('Failed to load latest metrics');
    }
  }

  /**
   * Get historical data for a specific metric
   */
  async getMetricHistory(
    metricName: string,
    hours: number = 24,
    maxPoints: number = 100
  ): Promise<MetricHistory[]> {
    try {
      const response: AxiosResponse<MetricHistory[]> = await api.get(
        `/dashboard/metrics/${encodeURIComponent(metricName)}/history`,
        {
          params: { hours, max_points: maxPoints },
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Failed to get metric history for ${metricName}:`, error);
      throw new Error(`Failed to load history for metric: ${metricName}`);
    }
  }

  /**
   * Get aggregated metrics over time intervals
   */
  async getAggregatedMetrics(
    metricName: string,
    hours: number = 24,
    interval: '5m' | '15m' | '1h' | '1d' = '1h',
    aggregationFunction: 'avg' | 'sum' | 'min' | 'max' | 'count' = 'avg'
  ): Promise<AggregatedMetric[]> {
    try {
      const response: AxiosResponse<AggregatedMetric[]> = await api.get(
        `/dashboard/metrics/${encodeURIComponent(metricName)}/aggregated`,
        {
          params: {
            hours,
            interval,
            function: aggregationFunction,
          },
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Failed to get aggregated metrics for ${metricName}:`, error);
      throw new Error(`Failed to load aggregated data for metric: ${metricName}`);
    }
  }

  /**
   * Get statistical analysis for a metric
   */
  async getMetricStatistics(
    metricName: string,
    hours: number = 24
  ): Promise<MetricStatistics> {
    try {
      const response: AxiosResponse<MetricStatistics> = await api.get(
        `/dashboard/metrics/${encodeURIComponent(metricName)}/statistics`,
        {
          params: { hours },
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Failed to get metric statistics for ${metricName}:`, error);
      throw new Error(`Failed to load statistics for metric: ${metricName}`);
    }
  }

  /**
   * Get metrics filtered by type
   */
  async getMetricsByType(
    metricType: string,
    hours: number = 24,
    limit: number = 100
  ): Promise<MetricData[]> {
    try {
      const response: AxiosResponse<MetricData[]> = await api.get(
        `/dashboard/metrics/types/${encodeURIComponent(metricType)}`,
        {
          params: { hours, limit },
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Failed to get metrics for type ${metricType}:`, error);
      throw new Error(`Failed to load metrics for type: ${metricType}`);
    }
  }

  /**
   * Get all available metrics for widget configuration
   */
  async getAvailableMetrics(): Promise<AvailableMetrics> {
    try {
      const response: AxiosResponse<AvailableMetrics> = await api.get(
        '/dashboard/widgets/available'
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get available metrics:', error);
      throw new Error('Failed to load available metrics');
    }
  }

  /**
   * Get dashboard widgets configuration
   */
  async getDashboardWidgets(isActive: boolean = true): Promise<DashboardWidget[]> {
    try {
      const response: AxiosResponse<DashboardWidget[]> = await api.get(
        '/dashboard/widgets',
        {
          params: { is_active: isActive },
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get dashboard widgets:', error);
      throw new Error('Failed to load dashboard widgets');
    }
  }

  /**
   * Create a new dashboard widget
   */
  async createWidget(config: WidgetConfiguration): Promise<DashboardWidget> {
    try {
      const response: AxiosResponse<DashboardWidget> = await api.post(
        '/dashboard/widgets',
        config
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create widget:', error);
      throw new Error('Failed to create dashboard widget');
    }
  }

  /**
   * Update existing dashboard widget
   */
  async updateWidget(
    widgetId: string,
    config: WidgetConfiguration
  ): Promise<DashboardWidget> {
    try {
      const response: AxiosResponse<DashboardWidget> = await api.put(
        `/dashboard/widgets/${widgetId}`,
        config
      );
      return response.data;
    } catch (error) {
      console.error('Failed to update widget:', error);
      throw new Error('Failed to update dashboard widget');
    }
  }

  /**
   * Delete dashboard widget
   */
  async deleteWidget(widgetId: string): Promise<void> {
    try {
      await api.delete(`/dashboard/widgets/${widgetId}`);
    } catch (error) {
      console.error('Failed to delete widget:', error);
      throw new Error('Failed to delete dashboard widget');
    }
  }

  /**
   * Populate sample data for development
   */
  async populateSampleData(): Promise<{ message: string; details: any }> {
    try {
      const response = await api.post('/dashboard/metrics/populate-sample-data');
      return response.data;
    } catch (error) {
      console.error('Failed to populate sample data:', error);
      throw new Error('Failed to populate sample data');
    }
  }

  /**
   * Start auto-refresh of dashboard data
   */
  startAutoRefresh(
    refreshCallback: () => Promise<void>,
    intervalMinutes: number = 5
  ): void {
    this.stopAutoRefresh();
    
    this.refreshConfig = {
      intervalMinutes,
      autoRefresh: true,
    };

    this.refreshIntervalId = setInterval(async () => {
      try {
        await refreshCallback();
      } catch (error) {
        console.error('Auto-refresh failed:', error);
      }
    }, intervalMinutes * 60 * 1000);

    console.log(`Auto-refresh started with ${intervalMinutes}-minute interval`);
  }

  /**
   * Stop auto-refresh
   */
  stopAutoRefresh(): void {
    if (this.refreshIntervalId) {
      clearInterval(this.refreshIntervalId);
      this.refreshIntervalId = null;
    }
    
    this.refreshConfig.autoRefresh = false;
    console.log('Auto-refresh stopped');
  }

  /**
   * Get current refresh configuration
   */
  getRefreshConfig(): DashboardRefreshConfig {
    return { ...this.refreshConfig };
  }

  /**
   * Check if auto-refresh is active
   */
  isAutoRefreshActive(): boolean {
    return this.refreshConfig.autoRefresh && this.refreshIntervalId !== null;
  }

  /**
   * Get comprehensive dashboard data
   */
  async getDashboardData(timeRangeHours: number = 24): Promise<{
    summary: DashboardSummary;
    widgets: DashboardWidget[];
    availableMetrics: AvailableMetrics;
  }> {
    try {
      const [summary, widgets, availableMetrics] = await Promise.all([
        this.getDashboardSummary(timeRangeHours),
        this.getDashboardWidgets(),
        this.getAvailableMetrics(),
      ]);

      return {
        summary,
        widgets,
        availableMetrics,
      };
    } catch (error) {
      console.error('Failed to get comprehensive dashboard data:', error);
      throw new Error('Failed to load dashboard data');
    }
  }

  /**
   * Get data for multiple metrics efficiently
   */
  async getMultipleMetricData(
    metricNames: string[],
    timeRangeHours: number = 24
  ): Promise<Record<string, MetricHistory[]>> {
    try {
      const promises = metricNames.map(name => 
        this.getMetricHistory(name, timeRangeHours).catch(error => {
          console.warn(`Failed to load data for metric ${name}:`, error);
          return [];
        })
      );

      const results = await Promise.all(promises);
      
      return metricNames.reduce((acc, name, index) => {
        acc[name] = results[index];
        return acc;
      }, {} as Record<string, MetricHistory[]>);
    } catch (error) {
      console.error('Failed to get multiple metric data:', error);
      throw new Error('Failed to load multiple metrics data');
    }
  }

  /**
   * Format metric value for display
   */
  formatMetricValue(value: number, unit?: string): string {
    if (typeof value !== 'number' || isNaN(value)) {
      return 'N/A';
    }

    let formattedValue: string;
    
    // Format based on value magnitude
    if (Math.abs(value) >= 1000000) {
      formattedValue = (value / 1000000).toFixed(1) + 'M';
    } else if (Math.abs(value) >= 1000) {
      formattedValue = (value / 1000).toFixed(1) + 'K';
    } else if (Math.abs(value) < 1 && Math.abs(value) > 0) {
      formattedValue = value.toFixed(3);
    } else {
      formattedValue = value.toFixed(1);
    }

    return unit ? `${formattedValue} ${unit}` : formattedValue;
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date);
    } catch (error) {
      console.error('Failed to format timestamp:', error);
      return timestamp;
    }
  }
}

// Create and export singleton instance
const dashboardService = new DashboardService();
export default dashboardService;