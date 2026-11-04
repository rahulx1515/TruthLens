import axios from 'axios';
import {
  AuthResponse,
  AnalysisResponse,
  AnalysisListResponse,
  DashboardStats,
  ModelsOverviewResponse,
  User,
} from '../types';

export const getGuestSessionId = (): string | null => {
  return localStorage.getItem('truthlens_guest_session_id');
};

export const getGuestClaimToken = (): string | null => {
  return localStorage.getItem('truthlens_guest_claim_token');
};

/**
 * Resolves the API base URL from VITE_API_URL or defaults to '/api/v1' for local development.
 * Ensures /api/v1 is appended exactly once regardless of backend hostname formatting.
 */
export const resolveApiBaseUrl = (rawUrl?: string): string => {
  const url = (rawUrl ?? (import.meta.env.VITE_API_URL as string | undefined) ?? '').trim();
  if (!url) {
    return '/api/v1';
  }
  const clean = url.replace(/\/+$/, '');
  if (clean.endsWith('/api/v1')) {
    return clean;
  }
  if (clean.endsWith('/api')) {
    return `${clean}/v1`;
  }
  return `${clean}/api/v1`;
};

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization token if stored, otherwise attach server-issued guest session ID if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('truthlens_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    const guestId = getGuestSessionId();
    if (guestId) {
      config.headers['X-Guest-Session-ID'] = guestId;
    }
  }
  return config;
});

// Response interceptor: automatically persist server-issued cryptographic guest tokens
api.interceptors.response.use(
  (response) => {
    const serverGuestId = response.headers['x-guest-session-id'];
    const serverClaimToken = response.headers['x-guest-claim-token'];

    if (serverGuestId) {
      localStorage.setItem('truthlens_guest_session_id', serverGuestId);
    }
    if (serverClaimToken) {
      localStorage.setItem('truthlens_guest_claim_token', serverClaimToken);
    }
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      const isAuthEndpoint = error.config?.url?.includes('/auth/login') || error.config?.url?.includes('/auth/register');
      if (!isAuthEndpoint) {
        localStorage.removeItem('truthlens_token');
        localStorage.removeItem('truthlens_user');
      }
    }
    return Promise.reject(error);
  }
);

export const claimGuestSessionReports = async () => {
  const guestId = getGuestSessionId();
  const claimToken = getGuestClaimToken();

  if (guestId && claimToken) {
    try {
      await api.post('/verify/claim-guest-reports', {
        guest_session_id: guestId,
        claim_token: claimToken,
      });
      localStorage.removeItem('truthlens_guest_session_id');
      localStorage.removeItem('truthlens_guest_claim_token');
    } catch {
      // Ignore claiming failure if guest session was empty or already transferred
    }
  }
};

export const authService = {
  async register(data: { email: string; password: string; full_name?: string }): Promise<User> {
    const res = await api.post<User>('/auth/register', data);
    return res.data;
  },
  async login(data: { email: string; password: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/login', data);
    if (res.data.access_token) {
      localStorage.setItem('truthlens_token', res.data.access_token);
      await claimGuestSessionReports();
    }
    return res.data;
  },
  async getMe(): Promise<User> {
    const res = await api.get<User>('/auth/me');
    localStorage.setItem('truthlens_user', JSON.stringify(res.data));
    return res.data;
  },
  logout() {
    localStorage.removeItem('truthlens_token');
    localStorage.removeItem('truthlens_user');
  },
};

export const analysisService = {
  async analyze(data: {
    title?: string;
    text?: string;
    url?: string;
    model_name?: string;
  }): Promise<AnalysisResponse> {
    const res = await api.post<AnalysisResponse>('/analyze', data);
    return res.data;
  },
  async getAnalyses(params?: {
    search?: string;
    filter?: string;
    page?: number;
    limit?: number;
  }): Promise<AnalysisListResponse> {
    const res = await api.get<AnalysisListResponse>('/analyses', { params });
    return res.data;
  },
  async getAnalysis(id: number): Promise<AnalysisResponse> {
    const res = await api.get<AnalysisResponse>(`/analyses/${id}`);
    return res.data;
  },
  async deleteAnalysis(id: number): Promise<void> {
    await api.delete(`/analyses/${id}`);
  },
};

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const res = await api.get<DashboardStats>('/dashboard/stats');
    return res.data;
  },
};

export const modelsService = {
  async getPerformance(): Promise<ModelsOverviewResponse> {
    const res = await api.get<ModelsOverviewResponse>('/models/performance');
    return res.data;
  },
};

export default api;
