import { createTheme, ThemeOptions } from '@mui/material/styles';

// Color palette
const colors = {
  primary: {
    main: '#1976d2',
    light: '#42a5f5',
    dark: '#1565c0',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#dc004e',
    light: '#ff4569',
    dark: '#9a0036',
    contrastText: '#ffffff',
  },
  background: {
    default: '#f5f5f5',
    paper: '#ffffff',
  },
  text: {
    primary: '#212121',
    secondary: '#757575',
  },
  success: {
    main: '#4caf50',
    light: '#81c784',
    dark: '#388e3c',
  },
  warning: {
    main: '#ff9800',
    light: '#ffb74d',
    dark: '#f57c00',
  },
  error: {
    main: '#f44336',
    light: '#e57373',
    dark: '#d32f2f',
  },
  info: {
    main: '#2196f3',
    light: '#64b5f6',
    dark: '#1976d2',
  },
};

// Dashboard-specific color scheme
export const dashboardColors = {
  chart: {
    primary: '#1976d2',
    secondary: '#dc004e',
    success: '#4caf50',
    warning: '#ff9800',
    error: '#f44336',
    info: '#2196f3',
    purple: '#9c27b0',
    teal: '#009688',
    orange: '#ff5722',
    indigo: '#3f51b5',
  },
  widget: {
    background: '#ffffff',
    border: '#e0e0e0',
    shadow: 'rgba(0, 0, 0, 0.1)',
  },
  metrics: {
    positive: '#4caf50',
    negative: '#f44336',
    neutral: '#757575',
  },
};

// Base theme configuration
const baseTheme: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: colors.primary,
    secondary: colors.secondary,
    background: colors.background,
    text: colors.text,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  spacing: 8,
  shape: {
    borderRadius: 8,
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
    },
  },
};

// Component customizations
const componentOverrides: ThemeOptions['components'] = {
  MuiAppBar: {
    styleOverrides: {
      root: {
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        '&:hover': {
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
        },
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        textTransform: 'none',
        fontWeight: 500,
        padding: '8px 16px',
      },
      containedPrimary: {
        '&:hover': {
          backgroundColor: colors.primary.dark,
        },
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: 8,
        },
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 16,
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
      },
    },
  },
  MuiDataGrid: {
    styleOverrides: {
      root: {
        border: 'none',
        '& .MuiDataGrid-cell': {
          borderColor: '#e0e0e0',
        },
        '& .MuiDataGrid-columnHeaders': {
          backgroundColor: '#fafafa',
          borderColor: '#e0e0e0',
        },
      },
    },
  },
};

// Create the main theme
export const theme = createTheme({
  ...baseTheme,
  components: componentOverrides,
});

// Dark theme variant
export const darkTheme = createTheme({
  ...baseTheme,
  palette: {
    mode: 'dark',
    primary: colors.primary,
    secondary: colors.secondary,
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  components: {
    ...componentOverrides,
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e1e1e',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
        },
      },
    },
  },
});

// Theme utilities
export const getTheme = (isDark: boolean) => (isDark ? darkTheme : theme);

// Responsive breakpoints
export const breakpoints = theme.breakpoints;

// Common spacing values
export const spacing = {
  xs: theme.spacing(1), // 8px
  sm: theme.spacing(2), // 16px
  md: theme.spacing(3), // 24px
  lg: theme.spacing(4), // 32px
  xl: theme.spacing(6), // 48px
};

// Z-index levels for layering
export const zIndex = {
  drawer: 1200,
  appBar: 1100,
  modal: 1300,
  snackbar: 1400,
  tooltip: 1500,
};