import api from './api';
import {
  VerificationJobStatus,
  VerificationReport,
  VerificationSubmitPayload,
} from '../types/verification';

export const verificationService = {
  /**
   * Submits news article text, headline, or URL for live evidence-based verification.
   */
  async submitVerification(payload: VerificationSubmitPayload): Promise<{
    job_id: string;
    status: string;
    current_step: string;
    progress_percent: number;
    status_url: string;
    report_url: string;
  }> {
    const res = await api.post('/verify', payload);
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
   * Lists past verification jobs.
   */
  async listHistory(limit: number = 20): Promise<Array<{
    job_id: string;
    headline: string | null;
    status: string;
    overall_verdict: string | null;
    overall_confidence: number | null;
    language: string;
    created_at: string;
  }>> {
    const res = await api.get('/verify', { params: { limit } });
    return res.data;
  },
};

