/**
 * TruthLens - Multilingual Evidence-Based Verification Types
 */

export type FinalVerdict = 'SUPPORTED' | 'REFUTED' | 'MIXED' | 'UNVERIFIED' | 'OUTDATED';

export type NLILabel = 'entailment' | 'contradiction' | 'neutral';

export interface NLIPassageEvaluation {
  passage_id: string;
  article_url: string;
  article_title: string;
  source_domain: string;
  publisher_name: string;
  quoted_passage: string;
  published_date: string | null;
  retrieved_at: string;
  nli_label: NLILabel;
  entailment_prob: number;
  contradiction_prob: number;
  neutral_prob: number;
  is_syndicated: boolean;
  cluster_id: string | null;
  relevance_score?: number;
  exact_quotation_verified?: boolean;
  source_type?: string;
  relation_explanation?: string;
  inference_method?: string;
}

export interface ClaimVerificationResult {
  claim_id: string;
  claim_text: string;
  claim_type: string;
  language: string;
  verdict: FinalVerdict;
  confidence: number;
  supporting_evidence_count: number;
  contradicting_evidence_count: number;
  evaluations: NLIPassageEvaluation[];
  explanation: string;
  why_verdict?: string;
  corroboration_score?: number;
  limitations?: string;
}

export interface VerificationReport {
  verification_id: string;
  original_title: string | null;
  original_content: string;
  detected_language: string;
  is_code_mixed: boolean;
  overall_verdict: FinalVerdict;
  overall_confidence: number;
  executive_summary: string;
  why_this_verdict?: string;
  limitations_and_uncertainty?: string;
  extraction_method?: string;
  nli_inference_method?: string;
  claims_total: number;
  claims_supported: number;
  claims_refuted: number;
  claims_unverified: number;
  claims_outdated: number;
  claim_results: ClaimVerificationResult[];
  search_providers_used: string[];
  created_at: string;
}

export interface VerificationJobStatus {
  job_id: string;
  status: 'QUEUED' | 'EXTRACTING' | 'SEARCHING' | 'RETRIEVING' | 'VERIFYING' | 'GENERATING_REPORT' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  current_step: string;
  progress_percent: number;
  error_message: string | null;
  overall_verdict: FinalVerdict | null;
  overall_confidence: number | null;
  created_at: string;
  updated_at: string;
  has_report: boolean;
  elapsed_seconds?: number;
  is_guest_session?: boolean;
}

export interface VerificationSubmitPayload {
  text?: string;
  headline?: string;
  url?: string;
  language?: string;
  guest_session_id?: string;
}

export interface VerificationHistoryItem {
  id: string;
  job_id: string;
  headline: string | null;
  detected_language: string;
  overall_verdict: FinalVerdict;
  overall_confidence: number;
  claims_total: number;
  claims_count?: number;
  supporting_sources_count?: number;
  contradicting_sources_count?: number;
  created_at: string;
}

export interface VerificationDayTrend {
  date: string;
  supported: number;
  refuted: number;
  mixed: number;
  unverified: number;
  outdated: number;
  total: number;
}

export interface VerificationDashboardStats {
  total_verifications: number;
  supported_count: number;
  refuted_count: number;
  mixed_count: number;
  unverified_count: number;
  outdated_count: number;
  supported_percentage: number;
  refuted_percentage: number;
  mixed_percentage: number;
  unverified_percentage: number;
  outdated_percentage: number;
  total_claims_investigated: number;
  avg_supporting_sources: number;
  avg_contradicting_sources: number;
  recent_verifications: VerificationHistoryItem[];
  daily_trend: VerificationDayTrend[];
}
