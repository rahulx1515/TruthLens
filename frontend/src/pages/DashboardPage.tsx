import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  ShieldCheck,
  FileText,
  Activity,
  PlusCircle,
  ExternalLink,
  Layers,
  HelpCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  TrendingUp,
  BarChart2,
  Globe,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts';
import { verificationService } from '../services/verificationApi';
import { VerificationDashboardStats } from '../types/verification';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<VerificationDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await verificationService.getVerificationStats();
        setStats(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to load verification analytics.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-sm text-slate-400">Loading intelligence dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-surface-card border border-rose-500/30 rounded-2xl p-8 text-center max-w-lg mx-auto space-y-4">
        <ShieldAlert className="w-10 h-10 text-rose-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">Analytics Unavailable</h3>
        <p className="text-sm text-slate-400">{error || 'Unable to retrieve live statistics.'}</p>
        <Link
          to="/verify"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg text-sm text-white font-medium hover:bg-blue-500"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Perform Verification</span>
        </Link>
      </div>
    );
  }

  const pieData = [
    { name: 'Supported', value: stats.supported_count, color: '#10b981' },
    { name: 'Refuted', value: stats.refuted_count, color: '#f43f5e' },
    { name: 'Mixed', value: stats.mixed_count, color: '#f59e0b' },
    { name: 'Unverified', value: stats.unverified_count, color: '#64748b' },
    { name: 'Outdated', value: stats.outdated_count, color: '#a855f7' },
  ].filter((item) => item.value > 0);

  const totalVerdictsCount = stats.total_verifications;

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <Activity className="w-7 h-7 text-blue-400" />
            <span>Verification Intelligence Dashboard</span>
          </h1>
          <p className="text-sm text-slate-400">
            Real-time evidence-backed verification analytics, claim distributions, and longitudinal trends
          </p>
        </div>
        <Link
          to="/verify"
          className="px-4 py-2.5 rounded-xl font-semibold text-sm text-white bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-600/25 flex items-center gap-2 transition-all"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Verify New Article</span>
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Verifications</span>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{stats.total_verifications}</div>
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>Articles investigated with live evidence</span>
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Claims Investigated</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-indigo-400">{stats.total_claims_investigated}</div>
          <div className="text-xs text-slate-400">
            Atomic factual claims verified
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Supported by Evidence</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400">{stats.supported_count}</div>
          <div className="text-xs text-slate-400">
            <span className="font-semibold text-emerald-400">{stats.supported_percentage}%</span> of investigated news
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Contradicted / Refuted</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400">{stats.refuted_count}</div>
          <div className="text-xs text-slate-400">
            <span className="font-semibold text-rose-400">{stats.refuted_percentage}%</span> refuted with evidence
          </div>
        </div>
      </div>

      {/* Secondary Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-surface-card/60 border border-surface-border rounded-xl p-4 flex items-center justify-between">
          <span className="text-xs text-slate-400">Mixed / Cherry-Picked Claims:</span>
          <span className="text-sm font-bold text-amber-400">{stats.mixed_count} ({stats.mixed_percentage}%)</span>
        </div>
        <div className="bg-surface-card/60 border border-surface-border rounded-xl p-4 flex items-center justify-between">
          <span className="text-xs text-slate-400">Unverified / Insufficient Evidence:</span>
          <span className="text-sm font-bold text-slate-400">{stats.unverified_count} ({stats.unverified_percentage}%)</span>
        </div>
        <div className="bg-surface-card/60 border border-surface-border rounded-xl p-4 flex items-center justify-between">
          <span className="text-xs text-slate-400">Avg Independent Sources / Claim:</span>
          <span className="text-sm font-bold text-blue-400 font-mono">
            {(stats.avg_supporting_sources + stats.avg_contradicting_sources).toFixed(1)}
          </span>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Verdict Distribution Pie */}
        <div className="lg:col-span-5 bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-blue-400" />
              <span>Verdict Distribution</span>
            </h2>
            <span className="text-xs text-slate-400">{totalVerdictsCount} verifications</span>
          </div>

          {totalVerdictsCount === 0 ? (
            <div className="py-16 text-center text-xs text-slate-400">
              No verification verdicts recorded yet. Run a verification to populate distribution charts.
            </div>
          ) : (
            <div className="h-64 relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0b0f19',
                      borderColor: '#1e293b',
                      borderRadius: '0.75rem',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap justify-center gap-3 text-xs pt-2">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  Supported ({stats.supported_count})
                </span>
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                  Refuted ({stats.refuted_count})
                </span>
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  Mixed ({stats.mixed_count})
                </span>
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
                  Unverified ({stats.unverified_count})
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Daily Verification Activity Bar Chart */}
        <div className="lg:col-span-7 bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Verification Activity (Last 7 Days)</span>
            </h2>
            <span className="text-xs text-slate-400">Daily verification volume</span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.daily_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0b0f19',
                    borderColor: '#1e293b',
                    borderRadius: '0.75rem',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="supported" name="Supported" fill="#10b981" stackId="a" radius={[0, 0, 0, 0]} />
                <Bar dataKey="refuted" name="Refuted" fill="#f43f5e" stackId="a" radius={[0, 0, 0, 0]} />
                <Bar dataKey="mixed" name="Mixed" fill="#f59e0b" stackId="a" radius={[0, 0, 0, 0]} />
                <Bar dataKey="unverified" name="Unverified" fill="#64748b" stackId="a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Verifications List */}
      <div className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-surface-border pb-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <span>Recent Verification Reports</span>
          </h2>
          <Link
            to="/history"
            className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors"
          >
            View all history →
          </Link>
        </div>

        {stats.recent_verifications.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            No verification reports available yet. Submit an article or claim on the Verify page.
          </div>
        ) : (
          <div className="divide-y divide-surface-border">
            {stats.recent_verifications.slice(0, 5).map((item) => (
              <div
                key={item.job_id}
                className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-900/40 px-2 rounded-lg transition-colors"
              >
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded ${
                        item.overall_verdict === 'SUPPORTED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : item.overall_verdict === 'REFUTED'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : item.overall_verdict === 'MIXED'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-slate-800 text-slate-400 border border-surface-border'
                      }`}
                    >
                      {item.overall_verdict}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {Math.round(item.overall_confidence * 100)}% Conf
                    </span>
                    <span className="text-[11px] text-slate-500">
                      • {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="text-xs sm:text-sm font-semibold text-slate-200 truncate max-w-xl">
                    {item.headline || 'Untitled Verification'}
                  </h3>
                </div>

                <button
                  type="button"
                  onClick={() => navigate(`/verify/${item.job_id}`)}
                  className="text-xs text-blue-400 hover:text-blue-300 font-medium inline-flex items-center gap-1 self-end sm:self-center shrink-0 hover:underline"
                >
                  <span>Open Report</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
