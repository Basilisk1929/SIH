/**
 * Authentication and RBAC API service.
 */

import { AuthTokens, User } from '../types';
import { ApiClient, clearStoredAuth, setStoredToken, USER_STORAGE_KEY } from './api';

export const AuthService = {
  async login(username: string, password: string, rememberMe = false): Promise<AuthTokens> {
    const data = await ApiClient.post<AuthTokens>('/auth/login-json', {
      email: username.trim(),
      password,
    }, {
      requiresAuth: false,
    });

    if (data.access_token) {
      setStoredToken(data.access_token, rememberMe);
    }
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const user = await ApiClient.get<User>('/auth/me');
    try {
      sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    } catch {
      // Storage restricted
    }
    return user;
  },

  async logout(): Promise<void> {
    try {
      await ApiClient.post('/auth/logout');
    } catch {
      // Clean local storage even if backend call fails
    } finally {
      clearStoredAuth();
    }
  },

  getStoredUserProfile(): User | null {
    try {
      const stored = sessionStorage.getItem(USER_STORAGE_KEY) || localStorage.getItem(USER_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  },
};
