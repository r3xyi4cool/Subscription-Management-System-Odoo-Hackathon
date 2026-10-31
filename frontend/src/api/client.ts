import { ApiErrorPayload } from './types';

export class ApiError extends Error {
  public code: string;
  public status: number;
  public fields?: Record<string, string[]>;

  constructor(status: number, errorPayload: ApiErrorPayload['error']) {
    super(errorPayload.message || 'An unexpected API error occurred');
    this.name = 'ApiError';
    this.status = status;
    this.code = errorPayload.code || 'unknown_error';
    this.fields = errorPayload.fields;
  }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Include CSRF token on mutating requests if present in cookies
  const csrfToken = getCookie('csrf_token');
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method?.toUpperCase() || '')) {
    headers.set('X-CSRF-Token', csrfToken);
  }

  // Pass standard Authorization header if auth token exists in localStorage
  const token = localStorage.getItem('auth_token');
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Always send cookies for real Flask HttpOnly session
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    let errorData: ApiErrorPayload['error'] = {
      code: 'http_error',
      message: response.statusText || 'Request failed',
    };

    try {
      const json = await response.json();
      if (json && json.error) {
        errorData = json.error;
      }
    } catch {
      // Non-json error response
    }

    if (response.status === 401) {
      localStorage.removeItem('auth_token');
      // Dispatch custom event for session expiry handling
      window.dispatchEvent(new CustomEvent('auth:expired', { detail: { message: errorData.message } }));
    }

    throw new ApiError(response.status, errorData);
  }

  // Handle empty responses (e.g. 204 No Content)
  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/pdf')) {
    const blob = await response.blob();
    return blob as unknown as T;
  }

  return response.json();
}
