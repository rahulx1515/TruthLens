export interface User {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface Article {
  id: number;
  title?: string;
  content: string;
  url?: string;
  domain?: string;
  author?: string;
  published_date?: string;
  created_at: string;
}

export interface IndicatorWord {
  word: string;
  importance: number;
  contribution: number;
  direction: 'fake' | 'real';
}

export interface ExplanationDetail {
  top_fake_indicators: IndicatorWord[];
  top_real_indicators: IndicatorWord[];
  summary: string;
}

export interface AnalysisResponse {
  id: number;
  prediction: 'FAKE' | 'REAL';
  label: 'Likely Fake' | 'Likely Authentic' | 'Inconclusive';
  confidence: number;
  probabilities: {
    fake: number;
    real: number;
  };
  model_name: string;
  model_version: string;
  processing_time_ms: number;
  explanation: ExplanationDetail;
  disclaimer: string;
  article?: Article;
  created_at?: string;
}

export interface AnalysisListItem {
  id: number;
  title?: string;
  url?: string;
  prediction: 'FAKE' | 'REAL';
  label: string;
  confidence: number;
  model_name: string;
  created_at: string;
}

export interface AnalysisListResponse {
  items: AnalysisListItem[];
  total: number;
  page: number;
  limit: number;
}

export interface DayDistribution {
  date: string;
  fake_count: number;
  authentic_count: number;
  total: number;
}

export interface DashboardStats {
  total_analyses: number;
  fake_count: number;
  authentic_count: number;
  fake_percentage: number;
  authentic_percentage: number;
  average_confidence: number;
  recent_analyses: AnalysisListItem[];
  daily_trend: DayDistribution[];
}

export interface ConfusionMatrixDetails {
  true_negative: number;
  false_positive: number;
  false_negative: number;
  true_positive: number;
  positive_label: string;
  negative_label: string;
  matrix: number[][];
}

export interface ModelBenchmarkItem {
  key: string;
  name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  latency_ms: number;
  confusion_matrix?: ConfusionMatrixDetails;
}

export interface ModelsOverviewResponse {
  selected_production_model: string;
  supported_models: string[];
  selection_rationale: string;
  dataset: string;
  vocabulary_size: number;
  models: ModelBenchmarkItem[];
}

