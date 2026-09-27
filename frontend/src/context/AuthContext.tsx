import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User, UserRole } from '../types';
import { AuthService } from '../services/auth';
import { clearStoredAuth, getStoredToken } from '../services/api';

export interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string, rememberMe?: boolean) => Promise<void>;
  logout: () => Promise<void>;
  isAdmin: boolean;
  isSupervisor: boolean;
  isInvestigator: boolean;
  isAnalyst: boolean;
  hasRole: (allowedRoles: UserRole[]) => boolean;
  canPerformAction: (action: 'CREATE_CASE' | 'UPDATE_CASE' | 'FREEZE_ACCOUNT' | 'RESOLVE_ALERT' | 'EXPORT_DOSSIER' | 'EXPORT_DATA' | 'VIEW_UNMASKED_PII') => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => AuthService.getStoredUserProfile());
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Sync session on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const activeToken = getStoredToken();
      if (!activeToken) {
        setUser(null);
        setToken(null);
        setIsLoading(false);
        return;
      }

      try {
        const profile = await AuthService.getCurrentUser();
        setUser(profile);
        setToken(activeToken);
      } catch {
        // Token invalid or expired
        clearStoredAuth();
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    // Listen to 401 expiration event dispatched by ApiClient
    const handleExpired = () => {
      setUser(null);
      setToken(null);
    };
    window.addEventListener('cybershield:auth-expired', handleExpired);

    return () => {
      window.removeEventListener('cybershield:auth-expired', handleExpired);
    };
  }, []);

  const login = useCallback(async (username: string, password: string, rememberMe = false) => {
    setIsLoading(true);
    try {
      const authTokens = await AuthService.login(username, password, rememberMe);
      setToken(authTokens.access_token);
      const profile = await AuthService.getCurrentUser();
      setUser(profile);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await AuthService.logout();
    } finally {
      setUser(null);
      setToken(null);
      setIsLoading(false);
    }
  }, []);

  const role = user?.role;

  const isAdmin = role === 'ADMIN';
  const isSupervisor = role === 'SUPERVISOR';
  const isInvestigator = role === 'INVESTIGATOR';
  const isAnalyst = role === 'ANALYST';

  const hasRole = useCallback(
    (allowedRoles: UserRole[]): boolean => {
      if (!role) return false;
      return allowedRoles.includes(role);
    },
    [role]
  );

  const canPerformAction = useCallback(
    (action: 'CREATE_CASE' | 'UPDATE_CASE' | 'FREEZE_ACCOUNT' | 'RESOLVE_ALERT' | 'EXPORT_DOSSIER' | 'EXPORT_DATA' | 'VIEW_UNMASKED_PII'): boolean => {
      if (!role) return false;
      switch (action) {
        case 'CREATE_CASE':
        case 'UPDATE_CASE':
          return ['ADMIN', 'SUPERVISOR', 'INVESTIGATOR'].includes(role);
        case 'FREEZE_ACCOUNT':
          return ['ADMIN', 'SUPERVISOR'].includes(role);
        case 'RESOLVE_ALERT':
          return ['ADMIN', 'SUPERVISOR', 'INVESTIGATOR'].includes(role);
        case 'EXPORT_DOSSIER':
        case 'EXPORT_DATA':
          return ['ADMIN', 'SUPERVISOR', 'INVESTIGATOR'].includes(role);
        case 'VIEW_UNMASKED_PII':
          return ['ADMIN', 'SUPERVISOR'].includes(role);
        default:
          return false;
      }
    },
    [role]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
        isAdmin,
        isSupervisor,
        isInvestigator,
        isAnalyst,
        hasRole,
        canPerformAction,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
