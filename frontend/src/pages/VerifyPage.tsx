import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Search,
  Globe,
  FileText,
  Link as LinkIcon,
  Sparkles,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  Clock,
  Layers,
  XCircle,
  ChevronDown,
  ChevronUp,
  UserCheck,
  RotateCcw,
  Info,
  LogIn,
  UserPlus,
} from 'lucide-react';
import { verificationService } from '../services/verificationApi';
import { VerificationJobStatus } from '../types/verification';
import { useAuth } from '../hooks/useAuth';

export const VerifyPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();

  const [activeTab, setActiveTab] = useState<'text' | 'url'>('text');
  const [headline, setHeadline] = useState('');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState<'auto' | 'en' | 'hi'>('auto');

  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<VerificationJobStatus | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showWhatHappening, setShowWhatHappening] = useState(false);

  // Client timer for elapsed seconds
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Poll active job status
  useEffect(() => {
    let interval: NodeJS.Timeout;
    const isJobActive =
      activeJobId &&
      jobStatus &&
      jobStatus.status !== 'COMPLETED' &&
      jobStatus.status !== 'FAILED' &&
      jobStatus.status !== 'CANCELLED';

    if (isJobActive) {
      interval = setInterval(async () => {
        try {
          const status = await verificationService.getStatus(activeJobId);
          setJobStatus(status);
          if (status.elapsed_seconds !== undefined) {
            setElapsedSeconds(status.elapsed_seconds);
          }
          if (status.status === 'COMPLETED' || status.status === 'FAILED' || status.status === 'CANCELLED') {
            clearInterval(interval);
            if (timerRef.current) clearInterval(timerRef.current);
          }
        } catch (err: any) {
          console.error('Polling status error:', err);
        }
      }, 1500);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeJobId, jobStatus?.status]);

  // Client-side elapsed timer tick
  useEffect(() => {
    if (activeJobId && jobStatus && jobStatus.status !== 'COMPLETED' && jobStatus.status !== 'FAILED' && jobStatus.status !== 'CANCELLED') {
      timerRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [activeJobId, jobStatus?.status]);

  const handleClear = () => {
    setHeadline('');
    setText('');
    setUrl('');
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    setElapsedSeconds(0);

    try {
      const payload = {
        headline: headline.trim() || undefined,
        text: activeTab === 'text' ? text.trim() || undefined : undefined,
        url: activeTab === 'url' ? url.trim() || undefined : undefined,
        language: language === 'auto' ? undefined : language,
      };

      if (!payload.text && !payload.url && !payload.headline) {
        throw new Error('Please enter news article text, a headline, or an article URL.');
      }

      if (payload.text && payload.text.length > 15000) {
        throw new Error('Input text exceeds maximum allowed size of 15,000 characters.');
      }

      const res = await verificationService.submitVerification(payload);
      setActiveJobId(res.job_id);
      setJobStatus({
        job_id: res.job_id,
        status: 'QUEUED',
        current_step: res.current_step,
        progress_percent: res.progress_percent,
        error_message: null,
        overall_verdict: null,
        overall_confidence: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        has_report: false,
        is_guest_session: !isAuthenticated,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit verification request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async () => {
    if (!activeJobId) return;
    setIsCancelling(true);
    try {
      await verificationService.cancelJob(activeJobId);
      setJobStatus((prev) => (prev ? { ...prev, status: 'CANCELLED', current_step: 'Verification cancelled by user.' } : null));
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to cancel job.');
    } finally {
      setIsCancelling(false);
    }
  };

  const handleRetry = async () => {
    if (!activeJobId) return;
    setError(null);
    setElapsedSeconds(0);
    try {
      await verificationService.retryJob(activeJobId);
      setJobStatus((prev) =>
        prev
          ? {
              ...prev,
              status: 'QUEUED',
              progress_percent: 0,
              current_step: 'Job queued for re-verification',
              error_message: null,
            }
          : null
      );
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Retry failed.');
    }
  };

  const sampleHindi = () => {
    setActiveTab('text');
    setLanguage('hi');
    setHeadline('ISRO चंद्रयान-3 मिशन');
    setText(
      'भारतीय अंतरिक्ष अनुसंधान संगठन (ISRO) ने पुष्टि की कि चंद्रयान-3 के प्रज्ञान रोवर ने चंद्रमा के दक्षिणी ध्रुव पर सल्फर की मौजूदगी का पता लगाया है।'
    );
  };

  const sampleEnglish = () => {
    setActiveTab('text');
    setLanguage('en');
    setHeadline('Federal Reserve Interest Rate Announcement');
    setText(
      'WASHINGTON - The Federal Reserve held its benchmark interest rate steady at 5.25% on Wednesday, noting that inflation has steadily decreased toward target levels in late 2024.'
    );
  };

  // Pipeline stages definition
  const pipelineStages = [
    {
      id: 1,
      key: 'EXTRACTING',
      name: 'Claim Extraction',
      description: 'Deconstructs input into discrete, testable factual propositions.',
    },
    {
      id: 2,
      key: 'SEARCHING',
      name: 'Live Evidence Discovery',
      description: 'Queries SearXNG, GDELT & RSS feeds with neutral and counter hypotheses.',
    },
    {
      id: 3,
      key: 'RETRIEVING',
      name: 'Article Retrieval and Filtering',
      description: 'Fetches original publisher pages, removes noise, and filters wire duplicates.',
    },
    {
      id: 4,
      key: 'VERIFYING',
      name: 'Evidence Relevance and NLI Verification',
      description: 'Verifies relevance and checks entailment/contradiction with cross-lingual NLI.',
    },
    {
      id: 5,
      key: 'GENERATING_REPORT',
      name: 'Report Generation',
      description: 'Synthesizes transparent final verdict with cited evidence audit trail.',
    },
  ];

  const getStageState = (stageKey: string, stageId: number) => {
    if (!jobStatus) return 'pending';
    if (jobStatus.status === 'COMPLETED') return 'completed';
    if (jobStatus.status === 'FAILED' || jobStatus.status === 'CANCELLED') {
      const stageOrder = ['QUEUED', 'EXTRACTING', 'SEARCHING', 'RETRIEVING', 'VERIFYING', 'GENERATING_REPORT'];
      const failedIdx = stageOrder.indexOf(jobStatus.status);
      if (stageId < failedIdx) return 'completed';
      if (stageId === failedIdx) return 'failed';
      return 'pending';
    }

    const stageMap: Record<string, number> = {
      QUEUED: 0,
      EXTRACTING: 1,
      SEARCHING: 2,
      RETRIEVING: 3,
      VERIFYING: 4,
      GENERATING_REPORT: 5,
    };

    const currentStageNum = stageMap[jobStatus.status] || 0;
    if (stageId < currentStageNum) return 'completed';
    if (stageId === currentStageNum) return 'active';
    return 'pending';
  };

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      {/* Guest Session Notice */}
      {!isAuthenticated && (
        <div className="bg-slate-900/90 border border-blue-500/30 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-md">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
              <UserCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-white flex items-center gap-2">
                <span>Guest Verification Session</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  Temporary
                </span>
              </div>
              <p className="text-xs text-slate-400">
                You can run up to 5 free verifications. Results remain available during this session.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              to="/login"
              className="text-xs font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-lg border border-surface-border hover:bg-slate-800 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="text-xs font-semibold text-white px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors shadow-sm"
            >
              Save History
            </Link>
          </div>
        </div>
      )}

      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multilingual Live Evidence Verification</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          Know What's True.{' '}
          <span className="bg-gradient-to-r from-blue-400 via-primary-500 to-indigo-300 bg-clip-text text-transparent">
            Verify With Evidence.
          </span>
        </h1>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
          Investigate news and factual claims using live sources, multilingual AI and transparent evidence.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Form Column */}
        <div className="lg:col-span-7 bg-[#0e1524] rounded-2xl border border-surface-border p-6 shadow-xl space-y-6">
          {/* Tabs & Language */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-surface-border pb-4">
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setActiveTab('text')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  activeTab === 'text'
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span>Paste Article / Claim</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('url')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  activeTab === 'url'
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <LinkIcon className="w-4 h-4" />
                <span>Article URL</span>
              </button>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 bg-slate-900 px-2.5 py-1.5 rounded-lg border border-surface-border text-xs">
                <Globe className="w-3.5 h-3.5 text-blue-400" />
                <select
                  aria-label="Verification language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as any)}
                  className="bg-transparent text-slate-200 outline-none cursor-pointer text-xs"
                >
                  <option value="auto" className="bg-slate-900">Auto-Detect</option>
                  <option value="en" className="bg-slate-900">English (en)</option>
                  <option value="hi" className="bg-slate-900">हिन्दी - Hindi (hi)</option>
                </select>
              </div>

              {(headline || text || url) && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                  title="Clear inputs"
                  aria-label="Clear inputs"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="headline-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Headline / Title (Optional)
              </label>
              <input
                id="headline-input"
                type="text"
                placeholder="e.g. Federal Reserve Holds Benchmark Rates Steady"
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900/90 border border-surface-border text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors text-sm"
              />
            </div>

            {activeTab === 'text' ? (
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="article-content-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Article Text or Factual Claims
                  </label>
                  <span className="text-xs text-slate-400 font-mono">
                    {wordCount} words • {charCount}/15,000 chars
                  </span>
                </div>
                <textarea
                  id="article-content-input"
                  rows={6}
                  maxLength={15000}
                  placeholder="Paste article body, quoted claims, or statements in English or Hindi (Devanagari)..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-surface-border text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors text-sm resize-y font-sans leading-relaxed"
                />
                <p className="text-[11px] text-slate-400 mt-1.5 flex items-center gap-1">
                  <Info className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Pasted text is verified against independently retrieved live web evidence.</span>
                </p>
              </div>
            ) : (
              <div>
                <label htmlFor="article-url-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Verified News Article URL
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Globe className="w-4 h-4" />
                  </div>
                  <input
                    id="article-url-input"
                    type="url"
                    placeholder="https://www.reuters.com/... or https://www.thehindu.com/..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/90 border border-surface-border text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1.5 flex items-center gap-1">
                  <Info className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>URL verification fetches and investigates the original article text with SSRF protection.</span>
                </p>
              </div>
            )}

            {/* Test Samples */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
              <span className="text-slate-400">Try sample:</span>
              <button
                type="button"
                onClick={sampleEnglish}
                className="px-2.5 py-1 rounded-md bg-slate-800 text-blue-300 hover:bg-slate-700 transition-colors"
              >
                English Economics News
              </button>
              <button
                type="button"
                onClick={sampleHindi}
                className="px-2.5 py-1 rounded-md bg-slate-800 text-emerald-300 hover:bg-slate-700 transition-colors"
              >
                हिन्दी अंतरिक्ष समाचार (ISRO)
              </button>
            </div>

            {error && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                <div>{error}</div>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting || (jobStatus && jobStatus.status !== 'COMPLETED' && jobStatus.status !== 'FAILED' && jobStatus.status !== 'CANCELLED')}
              className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Submitting to Live Verification Pipeline...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Start Live Evidence Verification</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Status / Tracker Column */}
        <div className="lg:col-span-5 bg-[#0e1524] rounded-2xl border border-surface-border p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between border-b border-surface-border pb-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              <span>Live Pipeline Monitor</span>
            </h2>
            {jobStatus && (
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-surface-border">
                  {jobStatus.job_id.substring(0, 14)}...
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {elapsedSeconds}s
                </span>
              </div>
            )}
          </div>

          {!jobStatus ? (
            <div className="text-center py-12 space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-800/80 mx-auto flex items-center justify-center text-slate-400">
                <Clock className="w-6 h-6" />
              </div>
              <p className="text-sm text-slate-300 font-medium">Ready for Investigation</p>
              <p className="text-xs text-slate-400 max-w-xs mx-auto">
                Submit news content to observe transparent claim extraction, live web search, and cross-lingual NLI verification.
              </p>
            </div>
          ) : (
            <div className="space-y-6 animate-fade-in">
              {/* Progress Bar & Status Text */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs font-medium">
                  <span className="text-slate-300 font-semibold">{jobStatus.current_step}</span>
                  <span className="text-blue-400 font-mono font-bold">{jobStatus.progress_percent}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 rounded-full ${
                      jobStatus.status === 'FAILED'
                        ? 'bg-rose-500'
                        : jobStatus.status === 'CANCELLED'
                        ? 'bg-amber-500'
                        : jobStatus.status === 'COMPLETED'
                        ? 'bg-emerald-500'
                        : 'bg-gradient-to-r from-blue-500 to-indigo-500'
                    }`}
                    style={{ width: `${Math.max(jobStatus.progress_percent, 5)}%` }}
                  />
                </div>
              </div>

              {/* 5 Distinct Pipeline Stages */}
              <div className="space-y-2.5">
                {pipelineStages.map((stage) => {
                  const state = getStageState(stage.key, stage.id);
                  const isDone = state === 'completed';
                  const isActive = state === 'active';
                  const isFailed = state === 'failed';

                  return (
                    <div
                      key={stage.id}
                      className={`flex items-start gap-3 p-3 rounded-xl text-xs transition-colors border ${
                        isDone
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                          : isActive
                          ? 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                          : isFailed
                          ? 'bg-rose-500/10 text-rose-300 border-rose-500/20'
                          : 'bg-slate-900/40 text-slate-500 border-surface-border/50'
                      }`}
                    >
                      <div className="mt-0.5 shrink-0">
                        {isDone ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        ) : isActive ? (
                          <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                        ) : isFailed ? (
                          <XCircle className="w-4 h-4 text-rose-400" />
                        ) : (
                          <div className="w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[10px] text-slate-500 font-mono">
                            {stage.id}
                          </div>
                        )}
                      </div>
                      <div className="space-y-0.5 flex-1">
                        <div className="font-semibold text-slate-200">{stage.id}. {stage.name}</div>
                        <div className="text-[11px] text-slate-400">{stage.description}</div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Active Job Controls: Cancel Option */}
              {jobStatus.status !== 'COMPLETED' && jobStatus.status !== 'FAILED' && jobStatus.status !== 'CANCELLED' && (
                <div className="flex justify-end pt-1">
                  <button
                    type="button"
                    onClick={handleCancel}
                    disabled={isCancelling}
                    className="text-xs text-slate-400 hover:text-rose-400 transition-colors flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-surface-border hover:border-rose-500/30"
                  >
                    {isCancelling ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
                    <span>Cancel Investigation</span>
                  </button>
                </div>
              )}

              {/* Completed State */}
              {jobStatus.status === 'COMPLETED' && (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                      Verdict: {jobStatus.overall_verdict}
                    </span>
                    <span className="text-xs text-slate-400">
                      Confidence: {Math.round((jobStatus.overall_confidence || 0) * 100)}%
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate(`/verify/${jobStatus.job_id}`)}
                    className="w-full py-2.5 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-colors flex items-center justify-center gap-2 shadow-md shadow-emerald-600/20"
                  >
                    <span>View Complete Verification Report</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {/* Failed or Cancelled State */}
              {(jobStatus.status === 'FAILED' || jobStatus.status === 'CANCELLED') && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 space-y-3">
                  <p className="text-xs text-rose-300">
                    {jobStatus.error_message || (jobStatus.status === 'CANCELLED' ? 'Verification cancelled by user.' : 'Verification job failed during execution.')}
                  </p>
                  <button
                    type="button"
                    onClick={handleRetry}
                    className="w-full py-2 px-3 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Retry Pipeline</span>
                  </button>
                </div>
              )}

              {/* Expandable "What is happening?" explanation */}
              <div className="pt-2 border-t border-surface-border">
                <button
                  type="button"
                  onClick={() => setShowWhatHappening(!showWhatHappening)}
                  className="w-full flex items-center justify-between text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors py-1"
                >
                  <span className="flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-blue-400" />
                    <span>What is happening during verification?</span>
                  </span>
                  {showWhatHappening ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {showWhatHappening && (
                  <div className="mt-3 p-3.5 rounded-xl bg-slate-900/80 border border-surface-border text-xs text-slate-300 space-y-2.5 animate-fade-in leading-relaxed">
                    <p>
                      <strong>1. Claim Extraction:</strong> The engine splits the text into concise, factual propositions and generates neutral queries as well as debunk-seeking counter queries.
                    </p>
                    <p>
                      <strong>2. Evidence Search:</strong> Searches trusted multi-tier sources across SearXNG, GDELT, and verified RSS feeds.
                    </p>
                    <p>
                      <strong>3. Publisher Scraping & Filtering:</strong> Downloads full articles from original publishers, rejects advertisements, and filters syndicated wire articles to prevent double-counting.
                    </p>
                    <p>
                      <strong>4. NLI Verification:</strong> A cross-lingual transformer computes entailment, contradiction, and neutrality scores between claims and evidence passages.
                    </p>
                    <p>
                      <strong>5. Transparent Verdict:</strong> Combines evidence into a traceable verdict (SUPPORTED, REFUTED, MIXED, or UNVERIFIED) with verbatim quotes.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
