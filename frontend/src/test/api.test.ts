import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ApiClient, ApiError, setStoredToken, getStoredToken, clearStoredAuth, TOKEN_STORAGE_KEY } from '../services/api';

describe('ApiClient & Authentication Token Layer', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('stores and retrieves JWT tokens properly', () => {
    setStoredToken('test-jwt-token-xyz', false);
    expect(getStoredToken()).toBe('test-jwt-token-xyz');
    expect(sessionStorage.getItem(TOKEN_STORAGE_KEY)).toBe('test-jwt-token-xyz');

    clearStoredAuth();
    expect(getStoredToken()).toBeNull();
  });

  it('attaches Authorization header when token is present', async () => {
    setStoredToken('jwt-bearer-12345');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'HEALTHY' }),
    });
    (globalThis as any).fetch = mockFetch;

    await ApiClient.get('/health');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const calledHeaders = mockFetch.mock.calls[0][1].headers;
    expect(calledHeaders.get('Authorization')).toBe('Bearer jwt-bearer-12345');
  });

  it('surfaces backend API errors and does NOT mask with silent fake data', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Account SYN999 not found' }),
    });
    (globalThis as any).fetch = mockFetch;

    await expect(ApiClient.get('/accounts/SYN999')).rejects.toThrow(ApiError);
    await expect(ApiClient.get('/accounts/SYN999')).rejects.toMatchObject({
      statusCode: 404,
      message: 'Account SYN999 not found',
    });
  });

  it('broadcasts cybershield:auth-expired on HTTP 401 Unauthorized', async () => {
    const expiredHandler = vi.fn();
    window.addEventListener('cybershield:auth-expired', expiredHandler);

    setStoredToken('expired-token');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Token signature expired' }),
    });
    (globalThis as any).fetch = mockFetch;

    await expect(ApiClient.get('/cases')).rejects.toThrow(ApiError);
    expect(expiredHandler).toHaveBeenCalled();
    expect(getStoredToken()).toBeNull();

    window.removeEventListener('cybershield:auth-expired', expiredHandler);
  });
});
