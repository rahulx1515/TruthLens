import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
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
} from 'lucide-react';
import { verificationService } from '../services/verificationApi';
import { VerificationJobStatus } from '../types/verification';

export const VerifyPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'text' | 'url'>('text');
  const [headline, setHeadline] = useState('');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState<'auto' | 'en' | 'hi'>('auto');

  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<VerificationJobStatus | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Poll active job status
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (activeJobId && (!jobStatus || (jobStatus.status !== 'COMPLETED' && jobStatus.status !== 'FAILED'))) {
      interval = setInterval(async () => {
        try {
          const status = await verificationService.getStatus(activeJobId);
          setJobStatus(status);
          if (status.status === 'COMPLETED') {
            clearInterval(interval);
          }
        } catch (err: any) {
          console.error('Polling error:', err);
        }
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeJobId, jobStatus]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    setJobStatus(null);

    try {
      const payload = {
        headline: headline.trim() || undefined,
        text: activeTab === 'text' ? text.trim() || undefined : undefined,
        url: activeTab === 'url' ? url.trim() || undefined : undefined,
        language: language === 'auto' ? undefined : language,
      };

      if (!payload.text && !payload.url && !payload.headline) {
        throw new Error('Please provide news text, headline, or article URL.');
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
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit verification job.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = async () => {
    if (!activeJobId) return;
    setError(null);
    try {
      await verificationService.retryJob(activeJobId);
      setJobStatus((prev) => (prev ? { ...prev, status: 'QUEUED', progress_percent: 0, error_message: null } : null));
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

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>TruthLens 2.0 Live Evidence Verification</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          Multilingual News <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">Verification Engine</span>
        </h1>
        <p className="text-slate-400 text-sm sm:text-base">
          Deconstructs articles into factual claims, retrieves live web evidence across SearXNG, GDELT & RSS,
          evaluates NLI entailment, and renders a fully transparent audit trail in English and Hindi.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Form Column */}
        <div className="lg:col-span-7 bg-[#0e1524] rounded-2xl border border-surface-border p-6 shadow-xl space-y-6">
          {/* Input Method Tabs */}
          <div className="flex items-center justify-between border-b border-surface-border pb-4">
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setActiveTab('text')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'text'
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span>Text / Social Claim</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('url')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'url'
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <LinkIcon className="w-4 h-4" />
                <span>Article URL</span>
              </button>
            </div>

            {/* Language Selector */}
            <div className="flex items-center gap-1.5 bg-slate-900 px-2.5 py-1 rounded-lg border border-surface-border text-xs">
              <Globe className="w-3.5 h-3.5 text-blue-400" />
              <select
                aria-label="Target verification language"
                value={language}
                onChange={(e) => setLanguage(e.target.value as any)}
                className="bg-transparent text-slate-200 outline-none cursor-pointer"
              >
                <option value="auto" className="bg-slate-900">Auto-Detect</option>
                <option value="en" className="bg-slate-900">English (en)</option>
                <option value="hi" className="bg-slate-900">हिन्दी - Hindi (hi)</option>
              </select>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="news-headline-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Headline / Title (Optional)
              </label>
              <input
                id="news-headline-input"
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
                  <label htmlFor="article-text-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Article Text or Claim Content
                  </label>
                  <span className="text-xs text-slate-400">{text.split(/\s+/).filter(Boolean).length} words</span>
                </div>
                <textarea
                  id="article-text-input"
                  rows={6}
                  placeholder="Paste article body, quoted claims, or social media statements in English, Hindi (Devanagari), or Hinglish..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-surface-border text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors text-sm resize-y font-sans leading-relaxed"
                />
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
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  SSRF protected with strict redirect revalidation and private CIDR blocking.
                </p>
              </div>
            )}

            {/* Samples */}
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
              disabled={isSubmitting || (jobStatus && jobStatus.status !== 'COMPLETED' && jobStatus.status !== 'FAILED')}
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
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-surface-border">
                {jobStatus.job_id}
              </span>
            )}
          </div>

          {!jobStatus ? (
            <div className="text-center py-12 space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-800/80 mx-auto flex items-center justify-center text-slate-400">
                <Clock className="w-6 h-6" />
              </div>
              <p className="text-sm text-slate-300 font-medium">Ready for Investigation</p>
              <p className="text-xs text-slate-400 max-w-xs mx-auto">
                Submit an article to observe real-time claim extraction, web evidence retrieval, and NLI verification.
              </p>
            </div>
          ) : (
            <div className="space-y-6 animate-fade-in">
              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-slate-300">{jobStatus.current_step}</span>
                  <span className="text-blue-400 font-mono">{jobStatus.progress_percent}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 rounded-full ${
                      jobStatus.status === 'FAILED'
                        ? 'bg-rose-500'
                        : jobStatus.status === 'COMPLETED'
                        ? 'bg-emerald-500'
                        : 'bg-gradient-to-r from-blue-500 to-indigo-500'
                    }`}
                    style={{ width: `${Math.max(jobStatus.progress_percent, 5)}%` }}
                  />
                </div>
              </div>

              {/* State Machine Steps */}
              <div className="space-y-3">
                {[
                  { key: 'EXTRACTING', label: '1. Factual Claim Extraction' },
                  { key: 'SEARCHING', label: '2. Multi-Tier Evidence Search' },
                  { key: 'RETRIEVING', label: '3. Article Chunking & Syndication Filter' },
                  { key: 'VERIFYING', label: '4. Multilingual NLI Verification' },
                  { key: 'GENERATING_REPORT', label: '5. Audit Trail & Report Synthesis' },
                ].map((step, idx) => {
                  const stepIndex = idx + 1;
                  const currentStageProgress = Math.floor(jobStatus.progress_percent / 20);
                  const isDone = currentStageProgress > stepIndex || jobStatus.status === 'COMPLETED';
                  const isCurrent = currentStageProgress === stepIndex && jobStatus.status !== 'COMPLETED' && jobStatus.status !== 'FAILED';

                  return (
                    <div
                      key={step.key}
                      className={`flex items-center gap-3 p-2.5 rounded-lg text-xs transition-colors ${
                        isDone
                          ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                          : isCurrent
                          ? 'bg-blue-500/10 text-blue-300 border border-blue-500/30'
                          : 'bg-slate-900/40 text-slate-400 border border-transparent'
                      }`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : isCurrent ? (
                        <RefreshCw className="w-4 h-4 text-blue-400 shrink-0 animate-spin" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-slate-600 shrink-0" />
                      )}
                      <span className="font-medium">{step.label}</span>
                    </div>
                  );
                })}
              </div>

              {/* Action buttons upon completion or failure */}
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

              {jobStatus.status === 'FAILED' && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 space-y-3">
                  <p className="text-xs text-rose-300">
                    {jobStatus.error_message || 'Verification job failed during execution.'}
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
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

