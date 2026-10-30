import api, { getGuestSessionId, getGuestClaimToken } from './api';
import {
  VerificationDashboardStats,
  VerificationHistoryItem,
  VerificationJobStatus,
  VerificationReport,
  VerificationSubmitPayload,
} from '../types/verification';

export const verificationService = {
  /**
   * Issues server-managed cryptographic guest session credentials.
   */
  async createGuestSession(): Promise<{ guest_session_id: string; claim_token: string; expires_at: string }> {
    const res = await api.post('/verify/guest-session');
    if (res.data?.guest_session_id && res.data?.claim_token) {
      localStorage.setItem('truthlens_guest_session_id', res.data.guest_session_id);
      localStorage.setItem('truthlens_guest_claim_token', res.data.claim_token);
    }
    return res.data;
  },

  /**
   * Submits news article text, headline, or URL for live evidence-based verification.
   * Scoped to user token or server-issued guest session ID.
   */
  async submitVerification(payload: VerificationSubmitPayload): Promise<{
    job_id: string;
    status: string;
    current_step: string;
    progress_percent: number;
    status_url: string;
    report_url: string;
  }> {
    const token = localStorage.getItem('truthlens_token');
    const guestId = getGuestSessionId();
    const enrichedPayload = {
      ...payload,
      guest_session_id: token ? undefined : (guestId || undefined),
    };
    const res = await api.post('/verify', enrichedPayload);
    return res.data;
  },

  /**
   * Polls the live verification job progress and state machine transitions.
   */
  async getStatus(jobId: string): Promise<VerificationJobStatus> {
    const res = await api.get<VerificationJobStatus>(`/verify/${jobId}/status`);
    return res.data;
  },

  /**
   * Retrieves the completed verification report and evidence audit trail.
   */
  async getReport(jobId: string): Promise<VerificationReport> {
    const res = await api.get<VerificationReport>(`/verify/${jobId}`);
    return res.data;
  },

  /**
   * Retries an interrupted or failed verification job without duplicate records.
   */
  async retryJob(jobId: string): Promise<{ job_id: string; status: string; message: string }> {
    const res = await api.post(`/verify/${jobId}/retry`);
    return res.data;
  },

  /**
   * Cancels an active verification job in flight.
   */
  async cancelJob(jobId: string): Promise<{ job_id: string; status: string; message: string }> {
    const res = await api.post(`/verify/${jobId}/cancel`);
    return res.data;
  },

  /**
   * Deletes a verification job and its report.
   */
  async deleteJob(jobId: string): Promise<{ message: string; deleted: boolean }> {
    const res = await api.delete(`/verify/${jobId}`);
    return res.data;
  },

  /**
   * Lists past verification jobs scoped to the current user or active guest session.
   */
  async listHistory(params?: {
    limit?: number;
    search?: string;
    verdict?: string;
  }): Promise<VerificationHistoryItem[]> {
    const res = await api.get<VerificationHistoryItem[]>('/verify', { params });
    return res.data;
  },

  /**
   * Associates prior anonymous guest verification records with the authenticated account.
   * Requires private cryptographic claim_token to prevent session takeover.
   */
  async claimGuestReports(guestSessionId: string, claimToken: string): Promise<{ claimed_count: number; message: string }> {
    const res = await api.post('/verify/claim-guest-reports', {
      guest_session_id: guestSessionId,
      claim_token: claimToken,
    });
    return res.data;
  },

  /**
   * Retrieves verification analytics and distribution metrics.
   */
  async getVerificationStats(): Promise<VerificationDashboardStats> {
    const res = await api.get<VerificationDashboardStats>('/dashboard/verification-stats');
    return res.data;
  },
};
