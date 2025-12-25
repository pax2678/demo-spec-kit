import React, { useState, useEffect } from 'react';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import {
  Box,
  Grid,
  Typography,
  Alert,
  CircularProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import MetricWidget from './MetricWidget';
import dashboardService, { DashboardWidget } from '../services/dashboardService';
import authService from '../services/authService';

// Make react-grid-layout responsive
const ResponsiveGridLayout = WidthProvider(Responsive);

interface MetricsGridProps {
  widgets?: DashboardWidget[];
  editable?: boolean;
  onLayoutChange?: (layouts: { [key: string]: Layout[] }) => void;
  onWidgetEdit?: (widget: DashboardWidget) => void;
  onWidgetDelete?: (widgetId: string) => void;
  loading?: boolean;
  error?: string | null;
}

interface GridItem extends Layout {
  widget: DashboardWidget;
}

const MetricsGrid: React.FC<MetricsGridProps> = ({
  widgets = [],
  editable = false,
  onLayoutChange,
  onWidgetEdit,
  onWidgetDelete,
  loading = false,
  error = null,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // 768px and below
  const isTablet = useMediaQuery(theme.breakpoints.down('md')); // 960px and below
  const isSmallMobile = useMediaQuery('(max-width:480px)'); // 480px and below
  const isTinyMobile = useMediaQuery('(max-width:320px)'); // 320px and below
  const is4K = useMediaQuery('(min-width:3840px)'); // 4K displays

  // State for grid layout
  const [layouts, setLayouts] = useState<{ [key: string]: Layout[] }>({});
  const [gridItems, setGridItems] = useState<GridItem[]>([]);

  // Convert widgets to grid items
  useEffect(() => {
    if (widgets.length === 0) {
      setGridItems([]);
      return;
    }

    const items: GridItem[] = widgets.map((widget, index) => ({
      i: widget.widget_id,
      x: widget.position_x || (index % 3) * 4,
      y: widget.position_y || Math.floor(index / 3) * 4,
      w: widget.width || 4,
      h: widget.height || 3,
      minW: 2,
      minH: 2,
      maxW: 12,
      maxH: 6,
      widget,
    }));

    setGridItems(items);

    // Set up responsive layouts
    const desktopLayouts = items.map(item => ({
      i: item.i,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
      minW: item.minW,
      minH: item.minH,
      maxW: item.maxW,
      maxH: item.maxH,
    }));

    // 4K layout - more columns
    const ultraWideLayouts = items.map((item, index) => ({
      i: item.i,
      x: (index % 6) * 2, // 6 columns for 4K
      y: Math.floor(index / 6) * 4,
      w: 2,
      h: 4,
      minW: 2,
      minH: 3,
      maxW: 4,
      maxH: 6,
    }));

    // Desktop layout - optimized for larger screens
    const desktopLayoutsOptimized = items.map(item => ({
      i: item.i,
      x: item.x,
      y: item.y,
      w: Math.min(item.w, 6), // Limit max width on desktop
      h: item.h,
      minW: item.minW,
      minH: item.minH,
      maxW: Math.min(item.maxW || 6, 6),
      maxH: item.maxH,
    }));

    // Tablet layout - 2 columns
    const tabletLayouts = items.map((item, index) => ({
      i: item.i,
      x: (index % 2) * 6,
      y: Math.floor(index / 2) * 3,
      w: 6,
      h: 3,
      minW: 6,
      minH: 2,
      maxW: 12,
      maxH: 4,
    }));

    // Mobile layout - single column
    const mobileLayouts = items.map((item, index) => ({
      i: item.i,
      x: 0,
      y: index * (isTinyMobile ? 2.5 : 3),
      w: 12,
      h: isTinyMobile ? 2.5 : 3,
      minW: 12,
      minH: isTinyMobile ? 2 : 2,
      maxW: 12,
      maxH: isTinyMobile ? 3 : 4,
    }));

    // Tiny mobile layout - very compact
    const tinyMobileLayouts = items.map((item, index) => ({
      i: item.i,
      x: 0,
      y: index * 2,
      w: 12,
      h: 2,
      minW: 12,
      minH: 2,
      maxW: 12,
      maxH: 2,
    }));

    setLayouts({
      xxl: ultraWideLayouts, // 4K displays
      xl: desktopLayoutsOptimized, // Large desktop
      lg: desktopLayoutsOptimized, // Desktop
      md: tabletLayouts, // Tablet
      sm: mobileLayouts, // Mobile
      xs: isTinyMobile ? tinyMobileLayouts : mobileLayouts, // Small mobile
      xxs: tinyMobileLayouts, // Tiny mobile (320px)
    });
  }, [widgets]);

  // Handle layout changes
  const handleLayoutChange = (layout: Layout[], allLayouts: { [key: string]: Layout[] }) => {
    setLayouts(allLayouts);
    
    if (onLayoutChange && editable) {
      onLayoutChange(allLayouts);
    }
  };

  // Handle widget editing
  const handleWidgetEdit = (widget: DashboardWidget) => {
    if (onWidgetEdit) {
      onWidgetEdit(widget);
    }
  };

  // Handle widget deletion
  const handleWidgetDelete = async (widgetId: string) => {
    if (onWidgetDelete) {
      onWidgetDelete(widgetId);
    }
  };

  // Render empty state
  const renderEmptyState = () => (
    <Box
      sx={{
        textAlign: 'center',
        py: 8,
        px: 2,
      }}
    >
      <Typography variant="h5" color="text.secondary" gutterBottom>
        No Widgets Configured
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        {editable 
          ? "Add some widgets to get started with your dashboard."
          : "No metrics are currently available to display."}
      </Typography>
      {editable && authService.isAnalyst() && (
        <Typography variant="body2" color="text.secondary">
          Use the "Add Widget" button to create your first metric visualization.
        </Typography>
      )}
    </Box>
  );

  // Render loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={48} />
      </Box>
    );
  }

  // Render error state
  if (error) {
    return (
      <Alert severity="error" sx={{ mx: 2, my: 4 }}>
        {error}
      </Alert>
    );
  }

  // Render empty state
  if (gridItems.length === 0) {
    return renderEmptyState();
  }

  // Grid breakpoints for responsive design
  const breakpoints = {
    xxl: 3840, // 4K displays
    xl: 1920,  // Large desktop
    lg: 1200,  // Desktop
    md: 960,   // Tablet
    sm: 768,   // Mobile
    xs: 480,   // Small mobile
    xxs: 320,  // Tiny mobile
  };

  // Columns for each breakpoint
  const cols = {
    xxl: 12,   // 4K - can fit more widgets
    xl: 12,    // Large desktop
    lg: 12,    // Desktop
    md: 12,    // Tablet
    sm: 12,    // Mobile
    xs: 12,    // Small mobile
    xxs: 12,   // Tiny mobile
  };

  // Row height for responsive design
  const getRowHeight = () => {
    if (isTinyMobile) return 60;   // Very compact for 320px
    if (isSmallMobile) return 70;  // Compact for small mobile
    if (isMobile) return 80;       // Mobile
    if (isTablet) return 100;      // Tablet
    if (is4K) return 140;          // Larger for 4K displays
    return 120;                    // Default desktop
  };

  return (
    <Box sx={{ width: '100%', minHeight: '400px' }}>
      {/* Grid Layout */}
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={breakpoints}
        cols={cols}
        rowHeight={getRowHeight()}
        onLayoutChange={handleLayoutChange}
        isDraggable={editable && !isMobile}
        isResizable={editable && !isMobile}
        margin={[16, 16]}
        containerPadding={[16, 16]}
        useCSSTransforms={true}
        preventCollision={false}
        compactType="vertical"
        style={{
          minHeight: '400px',
        }}
      >
        {gridItems.map((item) => (
          <div key={item.i}>
            <MetricWidget
              metricName={item.widget.metric_name}
              metricType={item.widget.metric_type}
              title={item.widget.title}
              description={item.widget.description}
              chartType={item.widget.configuration?.chartType || 'line'}
              timeRangeHours={item.widget.configuration?.timeRangeHours || 24}
              height={
                isTinyMobile ? 150 :
                isSmallMobile ? 180 :
                isMobile ? 200 : 
                isTablet ? 250 : 
                is4K ? 350 : 300
              }
              showMenu={editable && authService.isAnalyst() && !isTinyMobile}
              onEdit={() => handleWidgetEdit(item.widget)}
              onDelete={() => handleWidgetDelete(item.widget.widget_id)}
            />
          </div>
        ))}
      </ResponsiveGridLayout>

      {/* CSS for react-grid-layout */}
      <style>{`
        .react-grid-layout {
          position: relative;
        }
        
        .react-grid-item {
          transition: all 200ms ease;
          transition-property: left, top, width, height;
        }
        
        .react-grid-item.cssTransforms {
          transition-property: transform, width, height;
        }
        
        .react-grid-item > .react-resizable-handle {
          position: absolute;
          width: 20px;
          height: 20px;
          bottom: 0;
          right: 0;
          background: ${theme.palette.primary.main};
          background-image: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNiIgaGVpZ2h0PSI2IiB2aWV3Qm94PSIwIDAgNiA2IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Im0xIDUgNCAtNCIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEiLz48L3N2Zz4K');
          background-position: bottom right;
          background-repeat: no-repeat;
          background-origin: content-box;
          box-sizing: border-box;
          cursor: se-resize;
          border-radius: 0 0 4px 0;
          opacity: 0.8;
        }
        
        .react-grid-item > .react-resizable-handle:hover {
          opacity: 1;
        }
        
        .react-grid-item.react-grid-placeholder {
          background: ${theme.palette.primary.main};
          opacity: 0.2;
          transition-duration: 100ms;
          z-index: 2;
          user-select: none;
          border-radius: 4px;
        }
        
        .react-grid-item.react-draggable-dragging {
          transition: none;
          z-index: 3;
          opacity: 0.8;
        }
        
        .react-grid-item.react-resizable-resizing {
          transition: none;
          z-index: 3;
          opacity: 0.8;
        }
        
        .react-grid-item .MuiCard-root {
          height: 100%;
          cursor: ${editable && !isMobile ? 'move' : 'default'};
        }
        
        .react-grid-item .MuiCard-root:hover {
          box-shadow: ${editable ? theme.shadows[4] : theme.shadows[1]};
        }

        /* Mobile specific styles */
        @media (max-width: 768px) {
          .react-grid-item > .react-resizable-handle {
            display: none;
          }
          
          .react-grid-item .MuiCard-root {
            cursor: default;
          }
        }

        /* Tiny mobile styles (320px and below) */
        @media (max-width: 320px) {
          .react-grid-item {
            margin: 2px !important;
          }
          
          .react-grid-item .MuiCard-root {
            margin: 0;
          }
          
          .react-grid-layout {
            margin: 0 -2px;
          }
        }

        /* 4K display styles */
        @media (min-width: 3840px) {
          .react-grid-item .MuiCard-root {
            transition: box-shadow 0.3s ease;
          }
          
          .react-grid-item .MuiCard-root:hover {
            box-shadow: ${theme.shadows[8]};
            transform: translateY(-2px);
          }
        }

        /* High DPI displays */
        @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
          .react-grid-item .MuiTypography-root {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
          }
        }
      `}</style>
    </Box>
  );
};

export default MetricsGrid;