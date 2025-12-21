import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Button,
  Alert,
  Snackbar,
  Container,
  Grid,
  Paper,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  useMediaQuery,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Logout,
  Settings,
  Refresh,
  Dashboard as DashboardIcon,
  Add as AddIcon,
  FilterList,
  GetApp,
  Home,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import MetricsGrid from './MetricsGrid';
import dashboardService, { DashboardWidget } from '../services/dashboardService';
import authService, { User } from '../services/authService';

interface DashboardProps {
  title?: string;
  showHeader?: boolean;
  editable?: boolean;
}

const Dashboard: React.FC<DashboardProps> = ({
  title = 'Operational Dashboard',
  showHeader = true,
  editable = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // 768px and below
  const isTablet = useMediaQuery(theme.breakpoints.down('md')); // 960px and below  
  const isSmallMobile = useMediaQuery('(max-width:480px)'); // 480px and below for phones
  const isTinyMobile = useMediaQuery('(max-width:320px)'); // 320px for very small screens
  const is4K = useMediaQuery('(min-width:3840px)'); // 4K displays
  const navigate = useNavigate();

  // State management
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [user, setUser] = useState<User | null>(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Auto-refresh interval (5-15 minutes as per spec)
  const [autoRefreshInterval] = useState(5 * 60 * 1000); // 5 minutes

  // Load dashboard data
  const loadDashboard = useCallback(async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      // Load user info and dashboard widgets
      const [currentUser, dashboardWidgets] = await Promise.all([
        authService.getCurrentUser(),
        dashboardService.getDashboardWidgets(true),
      ]);

      setUser(currentUser);
      setWidgets(dashboardWidgets);
      setLastRefresh(new Date());
      
      if (showRefreshIndicator) {
        setSnackbarMessage('Dashboard updated successfully');
        setSnackbarOpen(true);
      }

    } catch (err) {
      console.error('Failed to load dashboard:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard';
      setError(errorMessage);
      
      if (showRefreshIndicator) {
        setSnackbarMessage(`Update failed: ${errorMessage}`);
        setSnackbarOpen(true);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Handle manual refresh
  const handleRefresh = useCallback(() => {
    loadDashboard(true);
  }, [loadDashboard]);

  // Handle logout
  const handleLogout = async () => {
    try {
      await authService.logout();
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
      setSnackbarMessage('Logout failed. Please try again.');
      setSnackbarOpen(true);
    }
    setUserMenuAnchor(null);
  };

  // Handle user menu
  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  // Handle layout changes (for customization)
  const handleLayoutChange = useCallback((layouts: { [key: string]: any[] }) => {
    if (editable && authService.isAnalyst()) {
      // Note: User preferences saving would be implemented based on backend API
      console.log('Layout changed:', layouts);
      setSnackbarMessage('Layout preferences saved');
      setSnackbarOpen(true);
    }
  }, [editable]);

  // Handle widget editing
  const handleWidgetEdit = (widget: DashboardWidget) => {
    // Navigate to widget configuration or open edit dialog
    console.log('Edit widget:', widget);
    setSnackbarMessage('Widget editing not yet implemented');
    setSnackbarOpen(true);
  };

  // Handle widget deletion
  const handleWidgetDelete = async (widgetId: string) => {
    try {
      await dashboardService.deleteWidget(widgetId);
      setWidgets(prev => prev.filter(w => w.widget_id !== widgetId));
      setSnackbarMessage('Widget removed successfully');
      setSnackbarOpen(true);
    } catch (err) {
      console.error('Failed to remove widget:', err);
      setSnackbarMessage('Failed to remove widget');
      setSnackbarOpen(true);
    }
  };

  // Handle add widget
  const handleAddWidget = () => {
    // Navigate to widget selection or open add dialog
    console.log('Add widget');
    setSnackbarMessage('Add widget functionality not yet implemented');
    setSnackbarOpen(true);
  };

  // Handle export
  const handleExport = () => {
    // Navigate to export page or open export dialog
    console.log('Export dashboard');
    setSnackbarMessage('Export functionality not yet implemented');
    setSnackbarOpen(true);
  };

  // Format last refresh time
  const formatLastRefresh = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes === 1) return '1 minute ago';
    if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
    
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    
    return date.toLocaleString();
  };

  // Effects
  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // Auto-refresh effect
  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboard(true);
    }, autoRefreshInterval);

    return () => clearInterval(interval);
  }, [loadDashboard, autoRefreshInterval]);

  // Render header
  const renderHeader = () => (
    <AppBar position="sticky" elevation={1}>
      <Toolbar>
        {/* Menu button for mobile */}
        {isMobile && (
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 1 }}
          >
            <MenuIcon />
          </IconButton>
        )}

        {/* Dashboard icon and title */}
        <DashboardIcon sx={{ mr: isTinyMobile ? 0.5 : 2 }} />
        <Typography 
          variant={isTinyMobile ? "subtitle1" : isSmallMobile ? "h6" : "h6"} 
          component="div" 
          sx={{ 
            flexGrow: 1,
            fontSize: isTinyMobile ? '0.9rem' : isSmallMobile ? '1.1rem' : '1.25rem',
            display: isTinyMobile ? '-webkit-box' : 'block',
            WebkitBoxOrient: 'vertical',
            WebkitLineClamp: isTinyMobile ? 1 : 'none',
            overflow: isTinyMobile ? 'hidden' : 'visible',
            textOverflow: 'ellipsis'
          }}
        >
          {isTinyMobile ? 'Dashboard' : title}
        </Typography>

        {/* Status indicators */}
        {!isTinyMobile && (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: isSmallMobile ? 0.5 : 1, 
            mr: isSmallMobile ? 1 : 2 
          }}>
            {/* Refresh status */}
            <Chip
              icon={<Refresh />}
              label={refreshing ? 'Updating...' : 
                isSmallMobile ? formatLastRefresh(lastRefresh).split(' ')[0] : 
                `Updated ${formatLastRefresh(lastRefresh)}`}
              size="small"
              variant="outlined"
              color={refreshing ? 'warning' : 'default'}
              sx={{ 
                color: 'inherit',
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '& .MuiChip-icon': { color: 'inherit' },
                fontSize: isSmallMobile ? '0.7rem' : '0.8125rem',
                height: isSmallMobile ? 24 : 32
              }}
            />

            {/* User role */}
            {user && !isSmallMobile && (
              <Chip
                label={user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                size="small"
                variant="filled"
                color="secondary"
              />
            )}
          </Box>
        )}

        {/* Action buttons */}
        <Box sx={{ 
          display: 'flex', 
          gap: isTinyMobile ? 0.25 : isSmallMobile ? 0.5 : 1
        }}>
          {/* Refresh button */}
          <IconButton
            color="inherit"
            onClick={handleRefresh}
            disabled={refreshing}
            title="Refresh Dashboard"
            size={isTinyMobile ? "small" : isSmallMobile ? "medium" : "large"}
          >
            <Refresh fontSize={isTinyMobile ? "small" : "medium"} />
          </IconButton>

          {/* Add widget button (for analysts and admins) */}
          {editable && authService.isAnalyst() && !isTinyMobile && (
            <IconButton
              color="inherit"
              onClick={handleAddWidget}
              title="Add Widget"
              size={isSmallMobile ? "medium" : "large"}
            >
              <AddIcon fontSize={isSmallMobile ? "small" : "medium"} />
            </IconButton>
          )}

          {/* Export button */}
          {!isTinyMobile && (
            <IconButton
              color="inherit"
              onClick={handleExport}
              title="Export Data"
              size={isSmallMobile ? "medium" : "large"}
            >
              <GetApp fontSize={isSmallMobile ? "small" : "medium"} />
            </IconButton>
          )}

          {/* User menu */}
          <IconButton
            size={isTinyMobile ? "medium" : isSmallMobile ? "large" : "large"}
            aria-label="account of current user"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={handleUserMenuOpen}
            color="inherit"
          >
            <AccountCircle fontSize={isTinyMobile ? "small" : "medium"} />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );

  // Render breadcrumbs
  const renderBreadcrumbs = () => (
    <Container maxWidth={false} sx={{ py: 2 }}>
      <Breadcrumbs aria-label="breadcrumb">
        <Link
          underline="hover"
          color="inherit"
          href="/"
          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
        >
          <Home fontSize="small" />
          Home
        </Link>
        <Typography
          color="text.primary"
          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
        >
          <DashboardIcon fontSize="small" />
          Dashboard
        </Typography>
      </Breadcrumbs>
    </Container>
  );

  // Render action bar
  const renderActionBar = () => (
    <Container maxWidth={false} sx={{ mb: 2 }}>
      <Paper elevation={1} sx={{ p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <Typography variant="h5" component="h1">
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Real-time operational metrics and system performance
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              {/* Filter button */}
              <Button
                startIcon={<FilterList />}
                variant="outlined"
                size="small"
                onClick={() => {
                  setSnackbarMessage('Filtering not yet implemented');
                  setSnackbarOpen(true);
                }}
              >
                Filter
              </Button>

              {/* Settings button (for admins) */}
              {authService.isAdmin() && (
                <Button
                  startIcon={<Settings />}
                  variant="outlined"
                  size="small"
                  onClick={() => navigate('/settings')}
                >
                  Settings
                </Button>
              )}

              {/* Add widget button */}
              {editable && authService.isAnalyst() && (
                <Button
                  startIcon={<AddIcon />}
                  variant="contained"
                  size="small"
                  onClick={handleAddWidget}
                >
                  Add Widget
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Header */}
      {showHeader && renderHeader()}

      {/* Breadcrumbs */}
      {showHeader && renderBreadcrumbs()}

      {/* Action Bar */}
      {showHeader && renderActionBar()}

      {/* Main Content */}
      <Container 
        maxWidth={is4K ? "xl" : false}
        sx={{ 
          flex: 1, 
          pb: isTinyMobile ? 2 : 4,
          px: { 
            xs: isTinyMobile ? 0.5 : 1, 
            sm: 2, 
            md: 3,
            lg: 4,
            xl: is4K ? 6 : 4
          },
          maxWidth: is4K ? '2400px' : '100%',
          margin: '0 auto'
        }}
      >
        {/* Error Alert */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 3 }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        {/* Metrics Grid */}
        <MetricsGrid
          widgets={widgets}
          loading={loading}
          error={error}
          editable={editable}
          onLayoutChange={handleLayoutChange}
          onWidgetEdit={handleWidgetEdit}
          onWidgetDelete={handleWidgetDelete}
        />
      </Container>

      {/* User Menu */}
      <Menu
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={handleUserMenuClose}
        onClick={handleUserMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
            '&:before': {
              content: '""',
              display: 'block',
              position: 'absolute',
              top: 0,
              right: 14,
              width: 10,
              height: 10,
              bgcolor: 'background.paper',
              transform: 'translateY(-50%) rotate(45deg)',
              zIndex: 0,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={() => navigate('/profile')}>
          <ListItemIcon>
            <AccountCircle fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            <Typography variant="body2">{user?.username || 'Profile'}</Typography>
            <Typography variant="caption" color="text.secondary">
              {user?.email}
            </Typography>
          </ListItemText>
        </MenuItem>

        <MenuItem onClick={() => navigate('/settings')}>
          <ListItemIcon>
            <Settings fontSize="small" />
          </ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>

        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default Dashboard;