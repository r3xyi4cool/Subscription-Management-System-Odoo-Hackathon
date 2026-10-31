import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User, UserRole } from '../api/types';
import { authApi } from '../api/endpoints';

interface AuthContextType {
  user: User | null;
  role: UserRole | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isStaff: boolean;
  isCustomer: boolean;
  login: (data: { email: string; password: string }) => Promise<void>;
  signup: (data: { email: string; password: string; name: string; phone?: string; company_name?: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  sessionExpiredMessage: string | null;
  clearSessionExpiredMessage: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionExpiredMessage, setSessionExpiredMessage] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await authApi.getMe();
      setUser(me);
    } catch {
      localStorage.removeItem('auth_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();

    const handleExpired = (e: Event) => {
      const customEvent = e as CustomEvent<{ message?: string }>;
      setUser(null);
      setSessionExpiredMessage(customEvent.detail?.message || 'Your session has expired. Please log in again.');
    };

    window.addEventListener('auth:expired', handleExpired);
    return () => window.removeEventListener('auth:expired', handleExpired);
  }, [refreshUser]);

  const login = async (data: { email: string; password: string }) => {
    setIsLoading(true);
    try {
      const res = await authApi.login(data);
      const token = res.access_token || res.session_token;
      if (token) {
        localStorage.setItem('auth_token', token);
      }
      setUser(res.user);
      setSessionExpiredMessage(null);
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (data: { email: string; password: string; name: string; phone?: string; company_name?: string }) => {
    setIsLoading(true);
    try {
      const res = await authApi.signup(data);
      const token = res.access_token || res.session_token;
      if (token) {
        localStorage.setItem('auth_token', token);
      }
      setUser(res.user);
      setSessionExpiredMessage(null);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('auth_token');
      setUser(null);
      window.location.href = '/login';
    }
  };

  const role = user?.role || null;
  const isAdmin = role === 'admin';
  const isStaff = role === 'staff';
  const isCustomer = role === 'customer';
  const isAuthenticated = Boolean(user && user.is_active);

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isLoading,
        isAuthenticated,
        isAdmin,
        isStaff,
        isCustomer,
        login,
        signup,
        logout,
        refreshUser,
        sessionExpiredMessage,
        clearSessionExpiredMessage: () => setSessionExpiredMessage(null),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
