/**
 * TruthLens 2.0 - Multilingual Evidence-Based Verification Types
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
  status: 'QUEUED' | 'EXTRACTING' | 'SEARCHING' | 'RETRIEVING' | 'VERIFYING' | 'GENERATING_REPORT' | 'COMPLETED' | 'FAILED';
  current_step: string;
  progress_percent: number;
  error_message: string | null;
  overall_verdict: FinalVerdict | null;
  overall_confidence: number | null;
  created_at: string;
  updated_at: string;
  has_report: boolean;
}

export interface VerificationSubmitPayload {
  text?: string;
  headline?: string;
  url?: string;
  language?: string;
}

