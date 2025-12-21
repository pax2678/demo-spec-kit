import axios, { AxiosResponse } from 'axios';

// API base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

// Configure axios defaults
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface User {
  user_id: string;
  username: string;
  email: string;
  role: 'viewer' | 'analyst' | 'admin';
  is_active: boolean;
  full_name: string;
  created_at?: string;
  last_login?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role?: 'viewer' | 'analyst' | 'admin';
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ChangePasswordData {
  old_password: string;
  new_password: string;
}

// Storage keys
const ACCESS_TOKEN_KEY = 'dashboard_access_token';
const REFRESH_TOKEN_KEY = 'dashboard_refresh_token';
const USER_KEY = 'dashboard_user';

class AuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private user: User | null = null;

  constructor() {
    this.loadTokensFromStorage();
    this.setupRequestInterceptor();
    this.setupResponseInterceptor();
  }

  /**
   * Load tokens and user data from localStorage
   */
  private loadTokensFromStorage(): void {
    this.accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    this.refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    
    const userData = localStorage.getItem(USER_KEY);
    if (userData) {
      try {
        this.user = JSON.parse(userData);
      } catch (error) {
        console.error('Failed to parse user data from storage:', error);
        this.clearStorage();
      }
    }
  }

  /**
   * Setup axios request interceptor to add auth header
   */
  private setupRequestInterceptor(): void {
    api.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  /**
   * Setup axios response interceptor for token refresh
   */
  private setupResponseInterceptor(): void {
    api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const original = error.config;

        if (error.response?.status === 401 && !original._retry) {
          original._retry = true;

          try {
            await this.refreshAccessToken();
            // Retry the original request with new token
            original.headers.Authorization = `Bearer ${this.accessToken}`;
            return api(original);
          } catch (refreshError) {
            // Refresh failed, logout user
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * Store tokens and user data in localStorage
   */
  private storeTokens(tokenResponse: TokenResponse, user: User): void {
    this.accessToken = tokenResponse.access_token;
    this.refreshToken = tokenResponse.refresh_token;
    this.user = user;

    localStorage.setItem(ACCESS_TOKEN_KEY, this.accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, this.refreshToken);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  /**
   * Clear tokens and user data from storage
   */
  private clearStorage(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.user = null;

    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  /**
   * Login user with credentials
   */
  async login(credentials: LoginCredentials): Promise<User> {
    try {
      // Prepare form data for OAuth2 password flow
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const tokenResponse: AxiosResponse<TokenResponse> = await api.post(
        '/auth/token',
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      // Get user information
      const tempToken = tokenResponse.data.access_token;
      const userResponse: AxiosResponse<User> = await api.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${tempToken}`,
        },
      });

      // Store tokens and user data
      this.storeTokens(tokenResponse.data, userResponse.data);

      return userResponse.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Login failed. Please check your credentials.'
      );
    }
  }

  /**
   * Register new user account
   */
  async register(userData: RegisterData): Promise<User> {
    try {
      const response: AxiosResponse<User> = await api.post('/auth/register', userData);
      
      // Auto-login after successful registration
      await this.login({
        username: userData.username,
        password: userData.password,
      });

      return response.data;
    } catch (error) {
      console.error('Registration failed:', error);
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Registration failed. Please try again.'
      );
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint if token exists
      if (this.accessToken) {
        await api.post('/auth/logout');
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Always clear local storage
      this.clearStorage();
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response: AxiosResponse<TokenResponse> = await api.post(
        '/auth/refresh',
        { refresh_token: this.refreshToken }
      );

      // Update access token
      this.accessToken = response.data.access_token;
      this.refreshToken = response.data.refresh_token;

      localStorage.setItem(ACCESS_TOKEN_KEY, this.accessToken);
      localStorage.setItem(REFRESH_TOKEN_KEY, this.refreshToken);
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearStorage();
      throw error;
    }
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    if (!this.accessToken) {
      throw new Error('No access token available');
    }

    try {
      const response: AxiosResponse<User> = await api.get('/auth/me');
      this.user = response.data;
      localStorage.setItem(USER_KEY, JSON.stringify(this.user));
      return response.data;
    } catch (error) {
      console.error('Get current user failed:', error);
      throw error;
    }
  }

  /**
   * Change user password
   */
  async changePassword(passwordData: ChangePasswordData): Promise<void> {
    try {
      await api.post('/auth/change-password', passwordData);
    } catch (error) {
      console.error('Change password failed:', error);
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to change password'
      );
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.accessToken && !!this.user;
  }

  /**
   * Get current user data
   */
  getUser(): User | null {
    return this.user;
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Check if user has specific role
   */
  hasRole(role: 'viewer' | 'analyst' | 'admin'): boolean {
    if (!this.user) return false;
    
    const roleHierarchy = {
      'viewer': 1,
      'analyst': 2,
      'admin': 3,
    };

    const userLevel = roleHierarchy[this.user.role] || 0;
    const requiredLevel = roleHierarchy[role] || 0;

    return userLevel >= requiredLevel;
  }

  /**
   * Check if user can perform admin actions
   */
  isAdmin(): boolean {
    return this.hasRole('admin');
  }

  /**
   * Check if user can perform analyst actions
   */
  isAnalyst(): boolean {
    return this.hasRole('analyst');
  }

  /**
   * Get user's display name
   */
  getUserDisplayName(): string {
    if (!this.user) return '';
    return this.user.full_name || this.user.username;
  }

  /**
   * Validate token and refresh if needed
   */
  async validateAuth(): Promise<boolean> {
    if (!this.accessToken) {
      return false;
    }

    try {
      // Try to get current user to validate token
      await this.getCurrentUser();
      return true;
    } catch (error) {
      // Token is invalid, try to refresh
      if (this.refreshToken) {
        try {
          await this.refreshAccessToken();
          await this.getCurrentUser();
          return true;
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
          this.clearStorage();
          return false;
        }
      }
      
      this.clearStorage();
      return false;
    }
  }
}

// Create and export singleton instance
const authService = new AuthService();
export default authService;