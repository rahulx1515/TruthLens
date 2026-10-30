import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Clock,
  ExternalLink,
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  Globe,
  Quote,
  CheckCircle2,
  XCircle,
  Layers,
  Info,
  Cpu,
  Share2,
  Check,
  UserPlus,
  LogIn,
  FileCheck,
} from 'lucide-react';
import { verificationService } from '../services/verificationApi';
import {
  FinalVerdict,
  NLIPassageEvaluation,
  VerificationReport,
} from '../types/verification';
import { useAuth } from '../hooks/useAuth';

export const VerificationReportPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [report, setReport] = useState<VerificationReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [evidenceFilter, setEvidenceFilter] = useState<'all' | 'entailment' | 'contradiction'>('all');
  const [copiedLink, setCopiedLink] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const fetchReport = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await verificationService.getReport(jobId);
        setReport(data);
      } catch (err: any) {
        setError(
          err.response?.data?.detail || err.message || 'Failed to retrieve verification report.'
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [jobId]);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="py-24 text-center space-y-4 animate-fade-in max-w-lg mx-auto">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
        <h2 className="text-lg font-semibold text-slate-200">Retrieving Verification Audit Trail...</h2>
        <p className="text-sm text-slate-400">
          Compiling claim assessments, publisher citations, and verified evidence passages.
        </p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-5 animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-white">Report Unavailable</h2>
        <p className="text-sm text-slate-400">{error || 'Could not load report.'}</p>
        <div className="flex justify-center gap-3 pt-2">
          <Link
            to="/verify"
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-colors inline-flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Verify</span>
          </Link>
        </div>
      </div>
    );
  }

  const getVerdictTheme = (verdict: FinalVerdict) => {
    switch (verdict) {
      case 'SUPPORTED':
        return {
          bg: 'bg-emerald-500/10',
          border: 'border-emerald-500/30',
          text: 'text-emerald-400',
          badgeBg: 'bg-emerald-500/20',
          icon: ShieldCheck,
          label: 'Supported by Live Evidence',
        };
      case 'REFUTED':
        return {
          bg: 'bg-rose-500/10',
          border: 'border-rose-500/30',
          text: 'text-rose-400',
          badgeBg: 'bg-rose-500/20',
          icon: ShieldAlert,
          label: 'Refuted by Live Evidence',
        };
      case 'MIXED':
        return {
          bg: 'bg-amber-500/10',
          border: 'border-amber-500/30',
          text: 'text-amber-400',
          badgeBg: 'bg-amber-500/20',
          icon: AlertTriangle,
          label: 'Mixed / Partially Contradicted',
        };
      case 'OUTDATED':
        return {
          bg: 'bg-purple-500/10',
          border: 'border-purple-500/30',
          text: 'text-purple-400',
          badgeBg: 'bg-purple-500/20',
          icon: Clock,
          label: 'Outdated / Superseded News',
        };
      case 'UNVERIFIED':
      default:
        return {
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/30',
          text: 'text-slate-400',
          badgeBg: 'bg-slate-500/20',
          icon: HelpCircle,
          label: 'Unverified / Insufficient Evidence',
        };
    }
  };

  const theme = getVerdictTheme(report.overall_verdict);
  const VerdictIcon = theme.icon;

  // Flatten all evaluations across claims for evidence explorer
  const allEvaluations: Array<{ claimText: string; ev: NLIPassageEvaluation }> = [];
  report.claim_results.forEach((cr) => {
    cr.evaluations.forEach((ev) => {
      allEvaluations.push({ claimText: cr.claim_text, ev });
    });
  });

  const filteredEvaluations = allEvaluations.filter((item) => {
    if (evidenceFilter === 'all') return true;
    return item.ev.nli_label === evidenceFilter;
  });

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* Guest Session CTA Banner */}
      {!isAuthenticated && (
        <div className="bg-gradient-to-r from-blue-900/30 via-slate-900 to-indigo-950/30 border border-blue-500/30 rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Your verification is complete</span>
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-300">
              Create a free account to save this report and access your verification history later.
            </p>
          </div>
          <div className="flex items-center gap-2.5 shrink-0">
            <Link
              to="/login"
              className="text-xs font-semibold text-slate-300 hover:text-white px-3.5 py-2 rounded-xl border border-surface-border hover:bg-slate-800 transition-colors inline-flex items-center gap-1.5"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </Link>
            <Link
              to="/register"
              className="text-xs font-semibold text-white px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-600/30 transition-all inline-flex items-center gap-1.5"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Create Account</span>
            </Link>
          </div>
        </div>
      )}

      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-5">
        <Link
          to="/verify"
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>New Verification</span>
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleCopyLink}
            className="text-xs font-medium px-3 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white border border-surface-border flex items-center gap-1.5 transition-colors"
          >
            {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Share2 className="w-3.5 h-3.5" />}
            <span>{copiedLink ? 'Link Copied' : 'Share Report'}</span>
          </button>
          <span className="text-[11px] font-mono px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-surface-border">
            ID: {report.verification_id.substring(0, 16)}...
          </span>
          <span className="text-[11px] font-medium px-2 py-1 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1">
            <Globe className="w-3 h-3" />
            {report.detected_language === 'hi' ? 'हिन्दी (Hindi)' : 'English (en)'}
            {report.is_code_mixed && ' • Hinglish'}
          </span>
        </div>
      </div>

      {/* Hero Verdict Card */}
      <div className={`rounded-2xl border ${theme.border} ${theme.bg} p-6 sm:p-8 shadow-2xl relative overflow-hidden`}>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className={`p-4 rounded-2xl ${theme.badgeBg} border ${theme.border} shrink-0`}>
              <VerdictIcon className={`w-10 h-10 ${theme.text}`} />
            </div>
            <div className="space-y-1.5">
              <span className={`text-xs font-bold uppercase tracking-wider ${theme.text}`}>
                TruthLens Final Verdict
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                {theme.label}
              </h1>
              {report.original_title && (
                <p className="text-sm font-medium text-slate-300 italic">
                  "{report.original_title}"
                </p>
              )}
            </div>
          </div>

          {/* Confidence Score Pill */}
          <div className="bg-slate-900/80 backdrop-blur-md px-5 py-3 rounded-2xl border border-surface-border text-center shrink-0 w-full md:w-auto">
            <div className="text-2xl font-black text-white font-mono">
              {Math.round(report.overall_confidence * 100)}%
            </div>
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Confidence Score
            </div>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="mt-6 pt-6 border-t border-slate-700/40 space-y-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Executive Verification Summary
          </h2>
          <p className="text-sm text-slate-200 leading-relaxed font-sans">
            {report.executive_summary}
          </p>
        </div>

        {/* Why This Verdict Section */}
        {report.why_this_verdict && (
          <div className="mt-5 p-4 rounded-xl bg-slate-900/70 border border-surface-border space-y-1.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5">
              <Info className="w-4 h-4" />
              <span>Why This Verdict?</span>
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {report.why_this_verdict}
            </p>
          </div>
        )}

        {/* Limitations & Uncertainty */}
        {report.limitations_and_uncertainty && (
          <div className="mt-3 p-3.5 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-300/90 leading-relaxed flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-amber-300">Limitations & Scope: </span>
              {report.limitations_and_uncertainty}
            </div>
          </div>
        )}

        {/* Pipeline Diagnostics & Providers Bar */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400 pt-4 border-t border-slate-700/30">
          <div className="flex flex-wrap items-center gap-2">
            <span>Discovery Sources:</span>
            {report.search_providers_used.map((p) => (
              <span
                key={p}
                className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-surface-border uppercase font-mono text-[10px]"
              >
                {p}
              </span>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {report.extraction_method && (
              <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-mono text-[10px] flex items-center gap-1">
                <Cpu className="w-3 h-3" />
                Extraction: {report.extraction_method === 'llm' ? 'Ollama LLM' : 'Rule-based'}
              </span>
            )}
            {report.nli_inference_method && (
              <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono text-[10px] flex items-center gap-1">
                <FileCheck className="w-3 h-3" />
                NLI: {report.nli_inference_method === 'neural' ? 'Neural Transformer' : 'Heuristic'}
              </span>
            )}
            <span>
              {new Date(report.created_at).toLocaleDateString()} {new Date(report.created_at).toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      {/* Claims Breakdown Section */}
      <div className="bg-[#0e1524] rounded-2xl border border-surface-border p-6 shadow-xl space-y-5">
        <div className="flex items-center justify-between border-b border-surface-border pb-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-400" />
            <span>Investigated Atomic Claims ({report.claims_total})</span>
          </h2>
          <div className="flex flex-wrap gap-2 text-xs">
            {report.claims_supported > 0 && (
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {report.claims_supported} Supported
              </span>
            )}
            {report.claims_refuted > 0 && (
              <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                {report.claims_refuted} Refuted
              </span>
            )}
            {report.claims_unverified > 0 && (
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-surface-border">
                {report.claims_unverified} Unverified
              </span>
            )}
            {report.claims_outdated > 0 && (
              <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                {report.claims_outdated} Outdated
              </span>
            )}
          </div>
        </div>

        <div className="space-y-4">
          {report.claim_results.map((cr, idx) => {
            const claimTheme = getVerdictTheme(cr.verdict);
            return (
              <div
                key={cr.claim_id}
                className="p-4 rounded-xl bg-slate-900/60 border border-surface-border hover:border-slate-700 transition-colors space-y-2.5"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-xs font-mono">
                      {idx + 1}
                    </span>
                    <span className="text-[11px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                      {cr.claim_type}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {cr.language.toUpperCase()}
                    </span>
                  </div>
                  <span
                    className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${claimTheme.bg} ${claimTheme.text} border ${claimTheme.border}`}
                  >
                    {cr.verdict}
                  </span>
                </div>

                <p className="text-sm font-semibold text-white leading-snug">
                  "{cr.claim_text}"
                </p>

                {cr.why_verdict ? (
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-surface-border/50">
                    <strong className="text-blue-400 font-medium">Verdict Rationale: </strong>
                    {cr.why_verdict}
                  </p>
                ) : (
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {cr.explanation}
                  </p>
                )}

                <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400 pt-1">
                  <span>
                    Supporting Sources: <strong className="text-emerald-400">{cr.supporting_evidence_count}</strong>
                  </span>
                  <span>
                    Contradicting Sources: <strong className="text-rose-400">{cr.contradicting_evidence_count}</strong>
                  </span>
                  {cr.corroboration_score !== undefined && (
                    <span>
                      Corroboration: <strong className="text-blue-400 font-mono">{Math.round(cr.corroboration_score * 100)}%</strong>
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Evidence Explorer & Passages Section */}
      <div className="bg-[#0e1524] rounded-2xl border border-surface-border p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Quote className="w-5 h-5 text-indigo-400" />
              <span>Evidence Passages & Exact Source Quotes</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Every quotation is verified verbatim against original publisher articles without LLM hallucination.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex gap-1.5 bg-slate-900 p-1 rounded-xl border border-surface-border text-xs">
            <button
              type="button"
              onClick={() => setEvidenceFilter('all')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                evidenceFilter === 'all' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              All ({allEvaluations.length})
            </button>
            <button
              type="button"
              onClick={() => setEvidenceFilter('entailment')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                evidenceFilter === 'entailment'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Supporting
            </button>
            <button
              type="button"
              onClick={() => setEvidenceFilter('contradiction')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                evidenceFilter === 'contradiction' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Contradicting
            </button>
          </div>
        </div>

        {filteredEvaluations.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            No evidence passages matching this filter.
          </div>
        ) : (
          <div className="space-y-5">
            {filteredEvaluations.map(({ claimText, ev }) => {
              const isEntailment = ev.nli_label === 'entailment';
              const isContradiction = ev.nli_label === 'contradiction';

              return (
                <div
                  key={ev.passage_id}
                  className="p-5 rounded-xl bg-slate-900/70 border border-surface-border space-y-3.5 hover:border-slate-700 transition-all"
                >
                  {/* Publisher & Source Link */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-white">{ev.publisher_name}</span>
                      <a
                        href={ev.article_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:text-blue-300 inline-flex items-center gap-1 font-mono hover:underline"
                      >
                        <span>{ev.source_domain}</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>

                    {/* NLI Badge & Source Badges */}
                    <div className="flex flex-wrap items-center gap-2">
                      {ev.source_type && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-surface-border">
                          {ev.source_type.replace('_', ' ')}
                        </span>
                      )}
                      {ev.exact_quotation_verified && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          Verbatim Verified
                        </span>
                      )}
                      {ev.is_syndicated && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          Syndicated Wire Copy
                        </span>
                      )}
                      <span
                        className={`text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1 ${
                          isEntailment
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : isContradiction
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-slate-800 text-slate-400 border border-surface-border'
                        }`}
                      >
                        {isEntailment && <CheckCircle2 className="w-3.5 h-3.5" />}
                        {isContradiction && <XCircle className="w-3.5 h-3.5" />}
                        <span className="uppercase font-mono text-[11px]">{ev.nli_label}</span>
                      </span>
                    </div>
                  </div>

                  {/* Verbatim Quoted Source Passage */}
                  <blockquote className="p-3.5 rounded-lg bg-[#0b0f19] border-l-4 border-blue-500 text-slate-200 text-sm italic leading-relaxed">
                    "{ev.quoted_passage}"
                  </blockquote>

                  {/* Relation Explanation */}
                  {ev.relation_explanation && (
                    <p className="text-xs text-slate-400 italic">
                      {ev.relation_explanation}
                    </p>
                  )}

                  {/* Metadata and Context */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400 pt-1">
                    <span className="truncate max-w-md">
                      Pertains to claim: <span className="text-slate-300 font-medium">"{claimText}"</span>
                    </span>
                    <div className="flex items-center gap-3 text-[11px]">
                      {ev.relevance_score !== undefined && (
                        <span>Relevance: <strong className="text-blue-300 font-mono">{Math.round(ev.relevance_score * 100)}%</strong></span>
                      )}
                      {ev.published_date && (
                        <span>Published: <strong className="text-slate-300">{ev.published_date}</strong></span>
                      )}
                      <span>Retrieved: <strong className="text-slate-300">{new Date(ev.retrieved_at).toLocaleDateString()}</strong></span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
