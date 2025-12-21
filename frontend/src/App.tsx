import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider, useAuth, ProtectedRoute } from './contexts/AuthContext';
import { theme } from './theme/theme';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Layout from './components/Layout';
import LoadingSpinner from './components/LoadingSpinner';

// Main app component with routing
const AppRoutes: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route 
          path="/login" 
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
          } 
        />

        {/* Protected routes */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute requiredRole="viewer">
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } 
        />

        {/* Admin routes */}
        <Route 
          path="/admin/*" 
          element={
            <ProtectedRoute 
              requiredRole="admin" 
              fallback={
                <Layout>
                  <div style={{ padding: '20px', textAlign: 'center' }}>
                    <h2>Access Denied</h2>
                    <p>Administrator privileges required to access this section.</p>
                  </div>
                </Layout>
              }
            >
              <Layout>
                <AdminRoutes />
              </Layout>
            </ProtectedRoute>
          } 
        />

        {/* Default redirects */}
        <Route 
          path="/" 
          element={
            <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
          } 
        />

        {/* 404 Not Found */}
        <Route 
          path="*" 
          element={
            <Layout>
              <div style={{ padding: '20px', textAlign: 'center' }}>
                <h2>404 - Page Not Found</h2>
                <p>The page you're looking for doesn't exist.</p>
                <a href="/dashboard">Go to Dashboard</a>
              </div>
            </Layout>
          } 
        />
      </Routes>
    </Router>
  );
};

// Admin-specific routes
const AdminRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<AdminDashboard />} />
      <Route path="/users" element={<UserManagement />} />
      <Route path="/system" element={<SystemMonitoring />} />
      <Route path="*" element={<Navigate to="/admin" replace />} />
    </Routes>
  );
};

// Placeholder admin components
const AdminDashboard: React.FC = () => (
  <div style={{ padding: '20px' }}>
    <h2>Admin Dashboard</h2>
    <p>Administrative tools and system overview will be implemented here.</p>
  </div>
);

const UserManagement: React.FC = () => (
  <div style={{ padding: '20px' }}>
    <h2>User Management</h2>
    <p>User administration tools will be implemented here.</p>
  </div>
);

const SystemMonitoring: React.FC = () => (
  <div style={{ padding: '20px' }}>
    <h2>System Monitoring</h2>
    <p>System health and monitoring tools will be implemented here.</p>
  </div>
);

// Main App component
const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;