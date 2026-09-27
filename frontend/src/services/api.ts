/**
 * Unified HTTP API client for CyberShield-Intel Frontend.
 *
 * Enforces:
 * - Configurable base URL via VITE_API_BASE_URL.
 * - Automatic Authorization: Bearer <token> attachment.
 * - Strict error surfacing (NO silent mock fallbacks on failure).
 * - Automatic 401 token invalidation handling.
 */

export class ApiError extends Error {
  statusCode: number;
  details?: any;

  constructor(message: string, statusCode: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

// Configurable API base URL (Vercel-ready)
export const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string') {
    return envUrl.replace(/\/+$/, '');
  }
  return '/api/v1';
};

// Token Storage Helpers (sessionStorage with fallback)
export const TOKEN_STORAGE_KEY = 'cybershield_auth_token';
export const USER_STORAGE_KEY = 'cybershield_user_profile';

export const getStoredToken = (): string | null => {
  try {
    return sessionStorage.getItem(TOKEN_STORAGE_KEY) || localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
};

export const setStoredToken = (token: string, persist = false): void => {
  try {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
    if (persist) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    }
  } catch {
    // Storage restricted
  }
};

export const clearStoredAuth = (): void => {
  try {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    sessionStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  } catch {
    // Ignore storage clear errors
  }
};

export interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { requiresAuth = true, headers: customHeaders, ...fetchOptions } = options;
  const baseUrl = getApiBaseUrl();

  // Normalize path
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${normalizedEndpoint}`;

  const headers = new Headers(customHeaders || {});

  // Set default JSON Content-Type if not already specified (e.g. For FormData)
  if (!headers.has('Content-Type') && !(fetchOptions.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Ensure tunnel gateways bypass reminder prompts
  headers.set('bypass-tunnel-reminder', 'true');

  // Attach JWT Bearer token if requested
  if (requiresAuth) {
    const token = getStoredToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers,
    });
  } catch (networkError: any) {
    throw new ApiError(
      `Network connection failed: Unable to connect to CyberShield backend at ${url}. ${networkError.message || ''}`,
      0
    );
  }

  // Handle 401 Unauthorized / Token Expiration
  if (response.status === 401) {
    clearStoredAuth();
    // Dispatch auth state change event for React AuthContext
    window.dispatchEvent(new CustomEvent('cybershield:auth-expired'));
    throw new ApiError('Session has expired or credentials are invalid. Please sign in again.', 401);
  }

  // Handle non-2xx HTTP errors
  if (!response.ok) {
    let errorDetail: any;
    let message = `Request failed with HTTP status ${response.status}`;
    try {
      errorDetail = await response.json();
      if (errorDetail?.detail) {
        message = typeof errorDetail.detail === 'string' ? errorDetail.detail : JSON.stringify(errorDetail.detail);
      } else if (errorDetail?.message) {
        message = errorDetail.message;
      }
    } catch {
      // Non-JSON response body
      message = await response.text().catch(() => message);
    }
    throw new ApiError(message, response.status, errorDetail);
  }

  // Parse JSON response
  if (response.status === 204) {
    return {} as T;
  }

  try {
    return await response.json();
  } catch (parseError: any) {
    throw new ApiError(`Failed to parse backend response as JSON: ${parseError.message}`, response.status);
  }
}

export const ApiClient = {
  get: <T>(endpoint: string, options?: RequestOptions) => request<T>(endpoint, { method: 'GET', ...options }),
  post: <T>(endpoint: string, data?: any, options?: RequestOptions) => {
    let body: any;
    if (data instanceof FormData || data instanceof URLSearchParams || typeof data === 'string') {
      body = data;
    } else if (data !== undefined) {
      body = JSON.stringify(data);
    }
    return request<T>(endpoint, {
      method: 'POST',
      body,
      ...options,
    });
  },
  patch: <T>(endpoint: string, data?: any, options?: RequestOptions) =>
    request<T>(endpoint, {
      method: 'PATCH',
      body: data instanceof FormData ? data : typeof data === 'string' ? data : JSON.stringify(data),
      ...options,
    }),
  put: <T>(endpoint: string, data?: any, options?: RequestOptions) =>
    request<T>(endpoint, {
      method: 'PUT',
      body: data instanceof FormData ? data : typeof data === 'string' ? data : JSON.stringify(data),
      ...options,
    }),
  delete: <T>(endpoint: string, options?: RequestOptions) => request<T>(endpoint, { method: 'DELETE', ...options }),
};

// Legacy compatibility helpers
export const formatINR = (val?: number): string => {
  if (val === undefined || isNaN(val)) return '₹0';
  return `₹${val.toLocaleString('en-IN')}`;
};

export const maskIdentifier = (val?: string): string => {
  if (!val) return 'N/A';
  if (val.length <= 4) return '****';
  return `${val.slice(0, 2)}****${val.slice(-2)}`;
};

export const ApiService = {
  getAccountSubgraph: (acc: string) => ApiClient.get<any>(`/graph/subgraph/${encodeURIComponent(acc)}?depth=2`),
  getComplaints: (limit = 15) => ApiClient.get<any>(`/complaints?limit=${limit}`),
};
