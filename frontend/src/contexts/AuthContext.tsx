import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService from '../services/authService';

// Types
interface User {
  user_id: string;
  username: string;
  email: string;
  role: 'admin' | 'viewer' | 'analyst';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  hasRole: (requiredRole: string) => boolean;
}

// Create context
const AuthContext = createContext<AuthContextType | null>(null);

// Role hierarchy for permission checking
const ROLE_HIERARCHY = {
  viewer: 1,
  analyst: 2,
  admin: 3,
};

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is authenticated
  const isAuthenticated = !!user && !!token;

  // authService already handles interceptors, no need to duplicate

  // Initialize auth state from authService
  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);

      if (authService.isAuthenticated()) {
        const userData = authService.getUser();
        const accessToken = authService.getAccessToken();

        if (userData && accessToken) {
          setUser(userData as User);
          setToken(accessToken);
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // Login function using authService
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);

      const userData = await authService.login({ username, password });

      setToken(authService.getAccessToken());
      setUser(userData as User);

      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function using authService
  const logout = () => {
    authService.logout();
    setToken(null);
    setUser(null);
  };

  // Refresh token function using authService
  const refreshToken = async (): Promise<boolean> => {
    try {
      await authService.refreshAccessToken();

      const userData = authService.getUser();
      const accessToken = authService.getAccessToken();

      if (userData && accessToken) {
        setUser(userData as User);
        setToken(accessToken);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  };

  // Check if user has required role
  const hasRole = (requiredRole: string): boolean => {
    if (!user || !user.role) {
      return false;
    }

    const userLevel = ROLE_HIERARCHY[user.role as keyof typeof ROLE_HIERARCHY] || 0;
    const requiredLevel = ROLE_HIERARCHY[requiredRole as keyof typeof ROLE_HIERARCHY] || 0;

    return userLevel >= requiredLevel;
  };

  const contextValue: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshToken,
    hasRole,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

// Higher-order component for protected routes
interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string;
  fallback?: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  fallback = <div>Access denied. Insufficient permissions.</div>,
}) => {
  const { isAuthenticated, hasRole, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <div>Please log in to access this page.</div>;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};