const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('spectra_token');
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let msg = res.statusText;
    try {
      const err = await res.json();
      msg = err.detail || err.message || msg;
    } catch {}
    throw new ApiError(res.status, msg);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  githubCallback: (code: string) =>
    request<import('@/types').TokenResponse>(`/api/v1/auth/github/callback?code=${code}`),
  me: () => request<import('@/types').User>('/api/v1/auth/me'),
};

// ─── Repos ────────────────────────────────────────────────────────────────────

export const reposApi = {
  list: () => request<import('@/types').Repo[]>('/api/v1/repos'),
  get: (id: string) => request<import('@/types').Repo>(`/api/v1/repos/${id}`),
  update: (id: string, body: import('@/types').RepoUpdate) =>
    request<import('@/types').Repo>(`/api/v1/repos/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  sync: () => request<import('@/types').Repo[]>('/api/v1/repos/sync', { method: 'POST' }),
};

// ─── Scans ────────────────────────────────────────────────────────────────────

export interface ScansListParams {
  repo_id?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export const scansApi = {
  list: (params: ScansListParams = {}) => {
    const q = new URLSearchParams();
    if (params.repo_id) q.set('repo_id', params.repo_id);
    if (params.status) q.set('status', params.status);
    if (params.page) q.set('page', String(params.page));
    if (params.page_size) q.set('page_size', String(params.page_size));
    return request<import('@/types').Scan[]>(`/api/v1/scans?${q}`);
  },
  get: (id: string) => request<import('@/types').Scan>(`/api/v1/scans/${id}`),
  trigger: (body: import('@/types').ManualScanRequest) =>
    request<import('@/types').Scan>('/api/v1/scans', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

// ─── Findings ─────────────────────────────────────────────────────────────────

export interface FindingsListParams {
  repo_id?: string;
  scan_id?: string;
  severity?: string;
  category?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export const findingsApi = {
  list: (params: FindingsListParams = {}) => {
    const q = new URLSearchParams();
    if (params.repo_id) q.set('repo_id', params.repo_id);
    if (params.scan_id) q.set('scan_id', params.scan_id);
    if (params.severity) q.set('severity', params.severity);
    if (params.category) q.set('category', params.category);
    if (params.status) q.set('status', params.status);
    if (params.page) q.set('page', String(params.page));
    if (params.page_size) q.set('page_size', String(params.page_size));
    return request<import('@/types').Finding[]>(`/api/v1/findings?${q}`);
  },
  get: (id: string) => request<import('@/types').Finding>(`/api/v1/findings/${id}`),
  update: (id: string, body: import('@/types').FindingUpdate) =>
    request<import('@/types').Finding>(`/api/v1/findings/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  bulkUpdate: (body: import('@/types').BulkFindingUpdate) =>
    request<import('@/types').Finding[]>('/api/v1/findings/bulk-update', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  events: (id: string) =>
    request<import('@/types').FindingEvent[]>(`/api/v1/findings/${id}/events`),
  autoFix: (id: string) =>
    request<import('@/types').Finding>(`/api/v1/findings/${id}/auto-fix`, { method: 'POST' }),
};

// ─── Analytics ─────────────────────────────────────────────────────────────────

export interface AnalyticsTrendsParams {
  repo_id?: string;
  period?: string;
}

export const analyticsApi = {
  trends: (params: AnalyticsTrendsParams = {}) => {
    const q = new URLSearchParams();
    if (params.repo_id) q.set('repo_id', params.repo_id);
    if (params.period) q.set('period', params.period);
    return request<import('@/types').AnalyticsResponse>(`/api/v1/analytics/trends?${q}`);
  },
};

// ─── Policies ──────────────────────────────────────────────────────────────────

export const policiesApi = {
  list: () => request<import('@/types').Policy[]>('/api/v1/policies'),
  create: (body: import('@/types').PolicyCreate) =>
    request<import('@/types').Policy>('/api/v1/policies', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  update: (id: string, body: import('@/types').PolicyUpdate) =>
    request<import('@/types').Policy>(`/api/v1/policies/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  delete: (id: string) =>
    request<void>(`/api/v1/policies/${id}`, { method: 'DELETE' }),
};
