import React, { useState, useContext } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
  Avatar,
  Link,
  Divider,
} from '@mui/material';
import { LockOutlined as LockIcon } from '@mui/icons-material';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import authService, { LoginCredentials } from '../services/authService';

interface LoginProps {
  onLoginSuccess?: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  
  // Form state
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: '',
  });
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDemoCredentials, setShowDemoCredentials] = useState(false);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!credentials.username.trim() || !credentials.password.trim()) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await authService.login(credentials);
      
      // Call success callback if provided
      if (onLoginSuccess) {
        onLoginSuccess();
      }
      
      // Navigate to dashboard
      navigate('/dashboard');
      
    } catch (error) {
      console.error('Login failed:', error);
      setError(
        error instanceof Error 
          ? error.message 
          : 'Login failed. Please check your credentials and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (demoUser: 'viewer' | 'analyst' | 'admin') => {
    const demoCredentials: Record<string, LoginCredentials> = {
      viewer: { username: 'demo_viewer', password: 'demo123' },
      analyst: { username: 'demo_analyst', password: 'demo123' },
      admin: { username: 'demo_admin', password: 'demo123' },
    };

    setCredentials(demoCredentials[demoUser]);
    
    // Auto-submit with demo credentials
    setLoading(true);
    setError(null);

    try {
      await authService.login(demoCredentials[demoUser]);
      
      if (onLoginSuccess) {
        onLoginSuccess();
      }
      
      navigate('/dashboard');
      
    } catch (error) {
      console.error('Demo login failed:', error);
      setError('Demo login failed. The demo account might not be set up.');
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = credentials.username.trim() && credentials.password.trim();

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          py: 3,
        }}
      >
        <Card
          sx={{
            width: '100%',
            maxWidth: 400,
            boxShadow: 3,
          }}
        >
          <CardContent sx={{ p: 4 }}>
            {/* Header */}
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                mb: 3,
              }}
            >
              <Avatar sx={{ m: 1, bgcolor: 'primary.main' }}>
                <LockIcon />
              </Avatar>
              <Typography component="h1" variant="h4" fontWeight="bold">
                Dashboard Login
              </Typography>
              <Typography variant="body2" color="text.secondary" textAlign="center">
                Sign in to access your operational metrics dashboard
              </Typography>
            </Box>

            {/* Error Alert */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {/* Login Form */}
            <Box component="form" onSubmit={handleSubmit} noValidate>
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                value={credentials.username}
                onChange={handleInputChange}
                disabled={loading}
                error={!!error && !credentials.username.trim()}
                helperText={
                  !credentials.username.trim() && error 
                    ? "Username is required"
                    : ""
                }
              />
              
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="current-password"
                value={credentials.password}
                onChange={handleInputChange}
                disabled={loading}
                error={!!error && !credentials.password.trim()}
                helperText={
                  !credentials.password.trim() && error 
                    ? "Password is required"
                    : ""
                }
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2, py: 1.5 }}
                disabled={!isFormValid || loading}
                startIcon={loading ? <CircularProgress size={20} /> : null}
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>

              {/* Demo Credentials Section */}
              <Box sx={{ mt: 2 }}>
                <Divider>
                  <Button 
                    size="small" 
                    onClick={() => setShowDemoCredentials(!showDemoCredentials)}
                    disabled={loading}
                  >
                    {showDemoCredentials ? 'Hide' : 'Show'} Demo Credentials
                  </Button>
                </Divider>
                
                {showDemoCredentials && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      Try the dashboard with demo accounts:
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleDemoLogin('viewer')}
                        disabled={loading}
                        sx={{ flex: 1, minWidth: 'fit-content' }}
                      >
                        Demo Viewer
                      </Button>
                      
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleDemoLogin('analyst')}
                        disabled={loading}
                        sx={{ flex: 1, minWidth: 'fit-content' }}
                      >
                        Demo Analyst
                      </Button>
                      
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleDemoLogin('admin')}
                        disabled={loading}
                        sx={{ flex: 1, minWidth: 'fit-content' }}
                      >
                        Demo Admin
                      </Button>
                    </Box>
                  </Box>
                )}
              </Box>

              {/* Additional Links */}
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Need an account?{' '}
                  <Link component={RouterLink} to="/register" color="primary">
                    Sign up here
                  </Link>
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  <Link component={RouterLink} to="/forgot-password" color="primary">
                    Forgot your password?
                  </Link>
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Footer */}
        <Typography 
          variant="caption" 
          color="text.secondary" 
          sx={{ mt: 3, textAlign: 'center' }}
        >
          Operational Metrics Dashboard v1.0.0
        </Typography>
      </Box>
    </Container>
  );
};

export default Login;