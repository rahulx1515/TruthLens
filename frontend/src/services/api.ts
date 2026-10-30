import axios from 'axios';
import {
  AuthResponse,
  AnalysisResponse,
  AnalysisListResponse,
  DashboardStats,
  ModelsOverviewResponse,
  User,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization token if stored
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('truthlens_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for session expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token if expired
      const isAuthEndpoint = error.config?.url?.includes('/auth/login') || error.config?.url?.includes('/auth/register');
      if (!isAuthEndpoint) {
        localStorage.removeItem('truthlens_token');
        localStorage.removeItem('truthlens_user');
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  async register(data: { email: string; password: string; full_name?: string }): Promise<User> {
    const res = await api.post<User>('/auth/register', data);
    return res.data;
  },
  async login(data: { email: string; password: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/login', data);
    if (res.data.access_token) {
      localStorage.setItem('truthlens_token', res.data.access_token);
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

