import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  History as HistoryIcon,
  Search,
  Filter,
  Trash2,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  HelpCircle,
  Clock,
  AlertCircle,
  PlusCircle,
  Globe,
  LogIn,
  UserPlus,
  RefreshCw,
  Layers,
} from 'lucide-react';
import { verificationService } from '../services/verificationApi';
import { FinalVerdict, VerificationHistoryItem } from '../types/verification';
import { useAuth } from '../hooks/useAuth';

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [historyItems, setHistoryItems] = useState<VerificationHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [verdictFilter, setVerdictFilter] = useState<string>('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await verificationService.listHistory({
        limit: 50,
        search: search.trim() || undefined,
        verdict: verdictFilter || undefined,
      });
      setHistoryItems(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load verification history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [verdictFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchHistory();
  };

  const handleDelete = async (jobId: string) => {
    if (!window.confirm('Are you sure you want to delete this verification record? This cannot be undone.')) {
      return;
    }
    setDeletingId(jobId);
    try {
      await verificationService.deleteJob(jobId);
      setHistoryItems((prev) => prev.filter((item) => item.job_id !== jobId));
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || 'Failed to delete verification.');
    } finally {
      setDeletingId(null);
    }
  };

  const getVerdictTheme = (verdict: FinalVerdict) => {
    switch (verdict) {
      case 'SUPPORTED':
        return {
          bg: 'bg-emerald-500/10',
          border: 'border-emerald-500/20',
          text: 'text-emerald-400',
          icon: ShieldCheck,
          label: 'Supported',
        };
      case 'REFUTED':
        return {
          bg: 'bg-rose-500/10',
          border: 'border-rose-500/20',
          text: 'text-rose-400',
          icon: ShieldAlert,
          label: 'Refuted',
        };
      case 'MIXED':
        return {
          bg: 'bg-amber-500/10',
          border: 'border-amber-500/20',
          text: 'text-amber-400',
          icon: AlertTriangle,
          label: 'Mixed',
        };
      case 'OUTDATED':
        return {
          bg: 'bg-purple-500/10',
          border: 'border-purple-500/20',
          text: 'text-purple-400',
          icon: Clock,
          label: 'Outdated',
        };
      case 'UNVERIFIED':
      default:
        return {
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/20',
          text: 'text-slate-400',
          icon: HelpCircle,
          label: 'Unverified',
        };
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-fade-in">
      {/* Guest Notice */}
      {!isAuthenticated && (
        <div className="bg-slate-900/90 border border-blue-500/30 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-md">
          <div className="space-y-0.5">
            <div className="text-xs font-semibold text-white flex items-center gap-2">
              <HistoryIcon className="w-4 h-4 text-blue-400" />
              <span>Guest Session History</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                Session Only
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Reports in this guest session are temporary and will clear when your browser session expires.
            </p>
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
              className="text-xs font-semibold text-white px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors"
            >
              Create Account
            </Link>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <HistoryIcon className="w-7 h-7 text-blue-400" />
            <span>Verification History</span>
          </h1>
          <p className="text-sm text-slate-400">
            Search, filter, and inspect your evidence-backed news verifications.
          </p>
        </div>
        <Link
          to="/verify"
          className="px-4 py-2.5 rounded-xl font-semibold text-xs text-white bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-600/25 transition-all inline-flex items-center gap-2"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Verification</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-surface-card border border-surface-border rounded-2xl p-4 flex flex-col sm:flex-row items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search headline or claim text..."
            className="w-full bg-[#0b0f19] border border-surface-border rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </form>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={verdictFilter}
            onChange={(e) => setVerdictFilter(e.target.value)}
            className="bg-[#0b0f19] border border-surface-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 w-full sm:w-auto"
          >
            <option value="">All Verdicts</option>
            <option value="SUPPORTED">Supported</option>
            <option value="REFUTED">Refuted</option>
            <option value="MIXED">Mixed</option>
            <option value="UNVERIFIED">Unverified</option>
            <option value="OUTDATED">Outdated</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <RefreshCw className="w-6 h-6 text-blue-500 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading verification history...</p>
        </div>
      ) : historyItems.length === 0 ? (
        /* Empty state */
        <div className="bg-surface-card border border-surface-border rounded-2xl p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
            <HistoryIcon className="w-6 h-6" />
          </div>
          <h2 className="text-base font-bold text-white">No Verifications Found</h2>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {search || verdictFilter
              ? 'No verification records match your search criteria. Try adjusting your filters.'
              : 'You have not submitted any news articles or claims for live verification yet.'}
          </p>
          <div className="pt-2">
            <Link
              to="/verify"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-all shadow-md shadow-blue-600/25"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Verify First Article</span>
            </Link>
          </div>
        </div>
      ) : (
        /* History Items List */
        <div className="space-y-3">
          {historyItems.map((item) => {
            const theme = getVerdictTheme(item.overall_verdict);
            const VerdictIcon = theme.icon;

            return (
              <div
                key={item.job_id}
                className="bg-surface-card border border-surface-border hover:border-slate-700 rounded-2xl p-4 sm:p-5 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${theme.bg} ${theme.text} border ${theme.border}`}
                    >
                      <VerdictIcon className="w-3.5 h-3.5" />
                      <span>{theme.label}</span>
                    </span>

                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-surface-border">
                      {Math.round(item.overall_confidence * 100)}% Confidence
                    </span>

                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1">
                      <Globe className="w-3 h-3" />
                      {item.detected_language === 'hi' ? 'HI' : 'EN'}
                    </span>
                  </div>

                  <h2 className="text-sm sm:text-base font-semibold text-white leading-snug">
                    {item.headline || 'Untitled News Verification'}
                  </h2>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5 text-blue-400" />
                      <span>{item.claims_count ?? item.claims_total} claims investigated</span>
                    </span>
                    {item.supporting_sources_count !== undefined && (
                      <span className="text-emerald-400 font-medium">
                        {item.supporting_sources_count} supporting sources
                      </span>
                    )}
                    {item.contradicting_sources_count !== undefined && (
                      <span className="text-rose-400 font-medium">
                        {item.contradicting_sources_count} contradicting sources
                      </span>
                    )}
                    <span className="text-slate-500">
                      {new Date(item.created_at).toLocaleDateString()} {new Date(item.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                  <button
                    type="button"
                    onClick={() => navigate(`/verify/${item.job_id}`)}
                    className="px-3.5 py-1.5 rounded-xl bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 hover:text-blue-300 border border-blue-500/30 text-xs font-semibold transition-colors flex items-center gap-1.5"
                  >
                    <span>View Report</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(item.job_id)}
                    disabled={deletingId === item.job_id}
                    title="Delete record"
                    className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors border border-transparent hover:border-rose-500/20"
                  >
                    {deletingId === item.job_id ? (
                      <RefreshCw className="w-4 h-4 animate-spin text-rose-400" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
