import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  ShieldCheck,
  FileText,
  Activity,
  PlusCircle,
  ArrowUpRight,
  TrendingUp,
  Clock,
  ExternalLink,
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
} from 'recharts';
import { dashboardService } from '../services/api';
import { DashboardStats } from '../types';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await dashboardService.getStats();
        setStats(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard analytics.');
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
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-400">Loading dashboard analytics...</p>
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
          to="/analyze"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg text-sm text-white font-medium hover:bg-blue-500"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Perform First Analysis</span>
        </Link>
      </div>
    );
  }

  const pieData = [
    { name: 'Likely Fake', value: stats.fake_count, color: '#f43f5e' },
    { name: 'Likely Authentic', value: stats.authentic_count, color: '#10b981' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Intelligence Dashboard</h1>
          <p className="text-sm text-slate-400">Real-time overview of credibility evaluations and trend distribution</p>
        </div>
        <Link
          to="/analyze"
          className="px-4 py-2.5 rounded-xl font-semibold text-sm text-white bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-600/25 flex items-center gap-2 transition-all"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Analysis</span>
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Evaluated</span>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{stats.total_analyses}</div>
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>Lifetime tracked articles</span>
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Likely Authentic</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400">{stats.authentic_count}</div>
          <div className="text-xs text-slate-400">
            <span className="font-semibold text-emerald-400">{stats.authentic_percentage}%</span> of evaluated corpus
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Likely Fabricated</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400">{stats.fake_count}</div>
          <div className="text-xs text-slate-400">
            <span className="font-semibold text-rose-400">{stats.fake_percentage}%</span> flagged as suspicious
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Confidence</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-indigo-300">
            {(stats.average_confidence * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
            <span>Model calibration certainty</span>
          </div>
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Activity Chart */}
        <div className="lg:col-span-2 bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white">7-Day Verification Volume</h3>
            <span className="text-xs font-mono text-slate-400">Real Backend Activity</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.daily_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2d42" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#1f2d42',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="authentic_count" name="Authentic" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fake_count" name="Fake" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Distribution Donut */}
        <div className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Prediction Breakdown</h3>
            <p className="text-xs text-slate-400">Authentic vs Fabricated ratio</p>
          </div>

          <div className="h-52 w-full relative flex items-center justify-center">
            {stats.total_analyses === 0 ? (
              <p className="text-xs text-slate-400">No predictions recorded yet</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: '#1f2d42',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-surface-border text-center">
            <div className="space-y-0.5">
              <span className="text-[11px] font-medium text-emerald-400">● Authentic</span>
              <p className="text-sm font-bold text-white">{stats.authentic_count}</p>
            </div>
            <div className="space-y-0.5">
              <span className="text-[11px] font-medium text-rose-400">● Fabricated</span>
              <p className="text-sm font-bold text-white">{stats.fake_count}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Analyses Table */}
      <div className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Recent Analyses</h3>
            <p className="text-xs text-slate-400">Most recently scanned news articles</p>
          </div>
          <Link
            to="/history"
            className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {stats.recent_analyses.length === 0 ? (
          <div className="text-center py-10 space-y-3">
            <p className="text-sm text-slate-400">No news analyses recorded yet.</p>
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg text-xs font-semibold text-white hover:bg-blue-500"
            >
              Analyze Your First Article
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-surface-border">
                <tr>
                  <th className="py-3 px-4">Headline / Source</th>
                  <th className="py-3 px-4">Prediction</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Model</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border/50 text-slate-300">
                {stats.recent_analyses.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-medium text-white max-w-xs truncate">
                      {item.title || 'Untitled Article'}
                      {item.url && (
                        <span className="block text-[11px] text-slate-400 truncate flex items-center gap-1">
                          <ExternalLink className="w-2.5 h-2.5 inline" /> {item.url}
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                          item.prediction === 'REAL'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {item.label}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-medium">
                      {(item.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400">{item.model_name}</td>
                    <td className="py-3.5 px-4 text-xs text-slate-400">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/analyze?resultId=${item.id}`}
                        className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                      >
                        View Report →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

