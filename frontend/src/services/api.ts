import type {
  ApiErrorBody,
  BlockchainHealthResponse,
  DashboardStats,
  HealthResponse,
  ModelDetail,
  ModelRegistration,
  ModelVersion,
  RecentActivityItem,
  TokenResponse,
  User,
  VerificationLog,
  VerificationResult,
} from '@/types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const TOKEN_KEY = 'verityai_access_token';

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

function detailMessage(body: ApiErrorBody | null, fallback: string): string {
  if (!body) return fallback;
  if (typeof body.detail === 'string') return body.detail;
  if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  if (body.error_code) return body.error_code;
  return fallback;
}

type RequestOptions = RequestInit & { auth?: boolean };

async function request<T>(path: string, init: RequestOptions = {}): Promise<T> {
  const { auth = false, ...fetchInit } = init;
  const headers = new Headers(fetchInit.headers);
  if (auth) {
    const token = getStoredToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }
  if (fetchInit.body && !(fetchInit.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, { ...fetchInit, headers });
  const text = await response.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = null;
    }
  }

  if (!response.ok) {
    const body = parsed as ApiErrorBody | null;
    throw new ApiError(
      detailMessage(body, `Request failed (${response.status})`),
      response.status,
      body?.error_code,
    );
  }

  return parsed as T;
}

export const api = {
  health: () => request<HealthResponse>('/api/v1/health'),
  blockchainHealth: () => request<BlockchainHealthResponse>('/api/v1/health/blockchain'),

  register: (payload: { email: string; password: string; display_name: string }) =>
    request<User>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: async (payload: { email: string; password: string }) => {
    const token = await request<TokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setStoredToken(token.access_token);
    return token;
  },

  logout: async () => {
    try {
      await request<{ detail: string }>('/api/v1/auth/logout', { method: 'POST', auth: true });
    } finally {
      setStoredToken(null);
    }
  },

  me: () => request<User>('/api/v1/auth/me', { auth: true }),

  dashboardStats: () => request<DashboardStats>('/api/v1/dashboard/stats', { auth: true }),

  recentActivity: () =>
    request<RecentActivityItem[]>('/api/v1/dashboard/recent-activity', { auth: true }),

  listModels: () => request<ModelDetail[]>('/api/v1/models', { auth: true }),

  getModel: (modelId: string) =>
    request<ModelDetail>(`/api/v1/models/${encodeURIComponent(modelId)}`, { auth: true }),

  modelHistory: (modelId: string) =>
    request<ModelVersion[]>(`/api/v1/models/${encodeURIComponent(modelId)}/history`, {
      auth: true,
    }),

  verificationHistory: (modelId: string) =>
    request<VerificationLog[]>(
      `/api/v1/models/${encodeURIComponent(modelId)}/verification-history`,
      { auth: true },
    ),

  registerModel: (form: FormData) =>
    request<ModelRegistration>('/api/v1/models/register', {
      method: 'POST',
      body: form,
      auth: true,
    }),

  registerVersion: (modelId: string, form: FormData) =>
    request<ModelRegistration>(`/api/v1/models/${encodeURIComponent(modelId)}/versions`, {
      method: 'POST',
      body: form,
      auth: true,
    }),

  verifyModel: (form: FormData) =>
    request<VerificationResult>('/api/v1/models/verify', { method: 'POST', body: form }),
};
