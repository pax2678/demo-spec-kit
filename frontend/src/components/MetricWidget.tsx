import React, { useEffect, useRef, useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  CircularProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  BarElement,
  ArcElement,
  Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import dashboardService, { MetricHistory, MetricSummary } from '../services/dashboardService';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

interface MetricWidgetProps {
  metricName: string;
  metricType: string;
  title: string;
  description?: string;
  chartType?: 'line' | 'bar' | 'doughnut' | 'stat';
  timeRangeHours?: number;
  height?: number;
  showMenu?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
  onRefresh?: () => void;
}

interface ChartData {
  labels: string[];
  datasets: any[];
}

const MetricWidget: React.FC<MetricWidgetProps> = ({
  metricName,
  metricType,
  title,
  description,
  chartType = 'line',
  timeRangeHours = 24,
  height = 300,
  showMenu = false,
  onEdit,
  onDelete,
  onRefresh,
}) => {
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metricHistory, setMetricHistory] = useState<MetricHistory[]>([]);
  const [summary, setSummary] = useState<MetricSummary | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  
  const chartRef = useRef<any>(null);

  // Load metric data
  const loadMetricData = async () => {
    setLoading(true);
    setError(null);

    try {
      const history = await dashboardService.getMetricHistory(
        metricName,
        timeRangeHours,
        100
      );
      
      setMetricHistory(history);
      
      // Create summary from history data
      if (history.length > 0) {
        const values = history.map(h => h.value);
        const latest = history[history.length - 1];
        
        setSummary({
          metric_name: metricName,
          current_value: latest.value,
          average: values.reduce((a, b) => a + b, 0) / values.length,
          minimum: Math.min(...values),
          maximum: Math.max(...values),
          count: values.length,
          unit: latest.unit,
          last_updated: latest.timestamp,
          trend: calculateTrend(values),
        });
      }
      
      setLastUpdated(new Date().toLocaleTimeString());
      
    } catch (err) {
      console.error('Failed to load metric data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load metric data');
    } finally {
      setLoading(false);
    }
  };

  // Calculate trend from values
  const calculateTrend = (values: number[]): 'increasing' | 'decreasing' | 'stable' => {
    if (values.length < 2) return 'stable';
    
    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));
    
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
    
    const changePercent = ((secondAvg - firstAvg) / firstAvg) * 100;
    
    if (changePercent > 5) return 'increasing';
    if (changePercent < -5) return 'decreasing';
    return 'stable';
  };

  // Prepare chart data
  const prepareChartData = (): ChartData => {
    const labels = metricHistory.map(h => 
      new Date(h.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      })
    );
    
    const values = metricHistory.map(h => h.value);
    
    const baseColor = getMetricColor();
    
    switch (chartType) {
      case 'line':
        return {
          labels,
          datasets: [{
            label: title,
            data: values,
            borderColor: baseColor,
            backgroundColor: `${baseColor}20`,
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5,
          }],
        };
        
      case 'bar':
        return {
          labels,
          datasets: [{
            label: title,
            data: values,
            backgroundColor: `${baseColor}80`,
            borderColor: baseColor,
            borderWidth: 1,
          }],
        };
        
      case 'doughnut':
        const latest = values[values.length - 1] || 0;
        const max = summary?.maximum || 100;
        return {
          labels: ['Current', 'Remaining'],
          datasets: [{
            data: [latest, max - latest],
            backgroundColor: [baseColor, `${baseColor}30`],
            borderWidth: 0,
          }],
        };
        
      default:
        return { labels: [], datasets: [] };
    }
  };

  // Get color based on metric type
  const getMetricColor = (): string => {
    const colorMap: Record<string, string> = {
      'system_performance': '#2196F3', // Blue
      'user_activity': '#4CAF50', // Green
      'error_rate': '#F44336', // Red
      'network': '#FF9800', // Orange
      'database': '#9C27B0', // Purple
    };
    
    return colorMap[metricType] || '#757575'; // Default gray
  };

  // Get trend icon
  const getTrendIcon = () => {
    if (!summary) return undefined;

    switch (summary.trend) {
      case 'increasing':
        return <TrendingUpIcon color="success" fontSize="small" />;
      case 'decreasing':
        return <TrendingDownIcon color="error" fontSize="small" />;
      default:
        return <TrendingFlatIcon color="info" fontSize="small" />;
    }
  };

  // Chart options
  const getChartOptions = () => {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          mode: 'index' as const,
          intersect: false,
          callbacks: {
            label: (context: any) => {
              const value = dashboardService.formatMetricValue(
                context.raw, 
                summary?.unit
              );
              return `${title}: ${value}`;
            },
          },
        },
      },
    };

    if (chartType === 'line' || chartType === 'bar') {
      return {
        ...baseOptions,
        scales: {
          x: {
            display: true,
            grid: {
              display: false,
            },
          },
          y: {
            display: true,
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)',
            },
            ticks: {
              callback: (value: any) => dashboardService.formatMetricValue(value, summary?.unit),
            },
          },
        },
        interaction: {
          mode: 'nearest' as const,
          axis: 'x' as const,
          intersect: false,
        },
      };
    }

    return baseOptions;
  };

  // Event handlers
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleRefresh = () => {
    loadMetricData();
    if (onRefresh) onRefresh();
    handleMenuClose();
  };

  const handleEdit = () => {
    if (onEdit) onEdit();
    handleMenuClose();
  };

  const handleDelete = () => {
    if (onDelete) onDelete();
    handleMenuClose();
  };

  // Effects
  useEffect(() => {
    loadMetricData();
  }, [metricName, metricType, timeRangeHours]);

  // Render stat widget
  const renderStatWidget = () => (
    <Box sx={{ textAlign: 'center', py: 2 }}>
      <Typography variant="h3" component="div" color="primary" fontWeight="bold">
        {summary ? dashboardService.formatMetricValue(summary.current_value, summary.unit) : '---'}
      </Typography>
      
      {summary && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            icon={getTrendIcon()}
            label={`${summary.trend.charAt(0).toUpperCase() + summary.trend.slice(1)}`}
            size="small"
            variant="outlined"
          />
          
          <Tooltip title={`Average: ${dashboardService.formatMetricValue(summary.average, summary.unit)}`}>
            <Chip
              label={`Avg: ${dashboardService.formatMetricValue(summary.average, summary.unit)}`}
              size="small"
              variant="outlined"
            />
          </Tooltip>
          
          <Tooltip title={`Min: ${dashboardService.formatMetricValue(summary.minimum, summary.unit)} | Max: ${dashboardService.formatMetricValue(summary.maximum, summary.unit)}`}>
            <Chip
              label={`${dashboardService.formatMetricValue(summary.minimum, summary.unit)} - ${dashboardService.formatMetricValue(summary.maximum, summary.unit)}`}
              size="small"
              variant="outlined"
            />
          </Tooltip>
        </Box>
      )}
    </Box>
  );

  // Render chart widget
  const renderChartWidget = () => {
    if (metricHistory.length === 0) {
      return (
        <Box sx={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography color="text.secondary">No data available</Typography>
        </Box>
      );
    }

    const chartData = prepareChartData();
    const chartOptions = getChartOptions();

    return (
      <Box sx={{ height }}>
        {chartType === 'line' && (
          <Line ref={chartRef} data={chartData} options={chartOptions} />
        )}
        {chartType === 'bar' && (
          <Bar ref={chartRef} data={chartData} options={chartOptions} />
        )}
        {chartType === 'doughnut' && (
          <Doughnut ref={chartRef} data={chartData} options={chartOptions} />
        )}
      </Box>
    );
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardHeader
        title={
          <Typography variant="h6" component="div" noWrap>
            {title}
          </Typography>
        }
        subheader={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              {description || metricName}
            </Typography>
            {lastUpdated && (
              <Typography variant="caption" color="text.secondary">
                • Updated: {lastUpdated}
              </Typography>
            )}
          </Box>
        }
        action={
          showMenu && (
            <IconButton onClick={handleMenuOpen} size="small">
              <MoreVertIcon />
            </IconButton>
          )
        }
        sx={{ pb: 1 }}
      />

      <CardContent sx={{ flex: 1, pt: 0, display: 'flex', flexDirection: 'column' }}>
        {loading ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: height || 200 }}>
            <CircularProgress size={40} />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : (
          <Box sx={{ flex: 1 }}>
            {chartType === 'stat' ? renderStatWidget() : renderChartWidget()}
          </Box>
        )}
      </CardContent>

      {/* Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleRefresh}>
          <RefreshIcon sx={{ mr: 1 }} fontSize="small" />
          Refresh
        </MenuItem>
        
        {onEdit && (
          <MenuItem onClick={handleEdit}>
            Edit Widget
          </MenuItem>
        )}
        
        {onDelete && (
          <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>
            Delete Widget
          </MenuItem>
        )}
      </Menu>
    </Card>
  );
};

export default MetricWidget;