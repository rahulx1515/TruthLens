import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  History,
  Search,
  Filter,
  Trash2,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
} from 'lucide-react';
import { analysisService } from '../services/api';
import { AnalysisListItem } from '../types';

export const HistoryPage: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await analysisService.getAnalyses({
        search: search.trim() || undefined,
        filter: filter || undefined,
        page,
        limit,
      });
      setAnalyses(data.items);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analysis history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, filter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchHistory();
  };

  const handleDelete = async (id: number) => {
    try {
      await analysisService.deleteAnalysis(id);
      setDeleteId(null);
      fetchHistory();
    } catch (err: any) {
      alert('Failed to delete analysis: ' + (err.response?.data?.detail || err.message));
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Analysis History</h1>
          <p className="text-sm text-slate-400">Search, filter, and inspect your previously evaluated news reports</p>
        </div>
        <Link
          to="/analyze"
          className="px-4 py-2.5 rounded-xl font-semibold text-xs text-white bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-600/25 transition-all"
        >
          + New Evaluation
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
            placeholder="Search headline or domain..."
            className="w-full bg-[#0b0f19] border border-surface-border rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </form>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value);
              setPage(1);
            }}
            className="bg-[#0b0f19] border border-surface-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 w-full sm:w-auto"
          >
            <option value="">All Predictions</option>
            <option value="REAL">Likely Authentic</option>
            <option value="FAKE">Likely Fabricated</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Table / List */}
      <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="py-16 text-center space-y-3">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-400">Loading history records...</p>
          </div>
        ) : analyses.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <History className="w-10 h-10 text-slate-500 mx-auto" />
            <h3 className="text-base font-semibold text-white">No records found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              {search || filter
                ? 'Try broadening your search query or filter options.'
                : 'You have not evaluated any news articles yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-[#0e1524] border-b border-surface-border">
                <tr>
                  <th className="py-3 px-5">Headline / Source</th>
                  <th className="py-3 px-4">Classification</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Engine</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border/50 text-slate-300">
                {analyses.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 px-5 font-medium text-white max-w-sm truncate">
                      <Link
                        to={`/analyze?resultId=${item.id}`}
                        className="hover:text-blue-400 transition-colors block truncate"
                      >
                        {item.title || 'Untitled News Article'}
                      </Link>
                      {item.url && (
                        <span className="text-[11px] text-slate-400 block truncate flex items-center gap-1 mt-0.5">
                          <ExternalLink className="w-3 h-3 inline" /> {item.url}
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold ${
                          item.prediction === 'REAL'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {item.prediction === 'REAL' ? (
                          <ShieldCheck className="w-3.5 h-3.5" />
                        ) : (
                          <ShieldAlert className="w-3.5 h-3.5" />
                        )}
                        {item.label}
                      </span>
                    </td>
                    <td className="py-4 px-4 font-mono font-medium text-slate-200">
                      {(item.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-4 px-4 text-xs text-slate-400">{item.model_name}</td>
                    <td className="py-4 px-4 text-xs text-slate-400">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-5 text-right space-x-2">
                      <Link
                        to={`/analyze?resultId=${item.id}`}
                        className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                      >
                        View
                      </Link>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                        title="Delete record"
                      >
                        <Trash2 className="w-3.5 h-3.5 inline" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {total > limit && (
          <div className="p-4 bg-[#0e1524] border-t border-surface-border flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {(page - 1) * limit + 1} - {Math.min(page * limit, total)} of {total} records
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1.5 rounded-lg border border-surface-border hover:bg-slate-800 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-mono px-2">
                {page} / {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="p-1.5 rounded-lg border border-surface-border hover:bg-slate-800 disabled:opacity-40 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

