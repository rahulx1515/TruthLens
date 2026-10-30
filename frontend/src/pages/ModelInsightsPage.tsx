import React, { useEffect, useState } from 'react';
import {
  BrainCircuit,
  Cpu,
  BarChart2,
  CheckCircle2,
  Layers,
  Zap,
  ShieldCheck,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { modelsService } from '../services/api';
import { ModelsOverviewResponse, ModelBenchmarkItem } from '../types';

export const ModelInsightsPage: React.FC = () => {
  const [data, setData] = useState<ModelsOverviewResponse | null>(null);
  const [selectedModelKey, setSelectedModelKey] = useState<string>('logistic_regression');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await modelsService.getPerformance();
        setData(res);
        if (res.models.length > 0) {
          setSelectedModelKey(res.models[0].key);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load model benchmarks.');
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-400">Loading validated model metrics...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-surface-card border border-rose-500/20 rounded-2xl p-8 text-center max-w-lg mx-auto space-y-3">
        <p className="text-sm text-rose-400">{error || 'Unable to load benchmark metrics.'}</p>
      </div>
    );
  }

  const selectedModel = data.models.find((m) => m.key === selectedModelKey) || data.models[0];

  const chartData = data.models.map((m) => ({
    name: m.name,
    Accuracy: m.accuracy,
    Precision: m.precision,
    Recall: m.recall,
    'F1-Score': m.f1_score,
  }));

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400">
          <BrainCircuit className="w-4 h-4" />
          <span>Audited Model Registry & Benchmarks</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Machine Learning Pipeline Insights
        </h1>
        <p className="text-sm text-slate-400">
          Comparative empirical evaluation across evaluated classifiers on {data.dataset} ({data.vocabulary_size.toLocaleString()} TF-IDF features).
        </p>
      </div>

      {/* Production Selection Alert */}
      <div className="bg-gradient-to-r from-blue-900/30 to-indigo-950/30 border border-blue-500/30 rounded-2xl p-6 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-bold text-white">
              Selected Production Engine: {data.selected_production_model}
            </h3>
          </div>
          <span className="text-[11px] font-mono font-bold bg-blue-500/20 text-blue-400 px-2.5 py-1 rounded-full border border-blue-500/30">
            ACTIVE INFERENCE
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">{data.selection_rationale}</p>
      </div>

      {/* Comparison Table */}
      <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden shadow-xl">
        <div className="p-5 border-b border-surface-border">
          <h3 className="text-base font-bold text-white">Empirical Evaluation Metrics</h3>
          <p className="text-xs text-slate-400">Validated test set performance on holdout samples (80/20 split)</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-[#0e1524] border-b border-surface-border">
              <tr>
                <th className="py-3 px-5">Model Architecture</th>
                <th className="py-3 px-4">Accuracy</th>
                <th className="py-3 px-4">Precision</th>
                <th className="py-3 px-4">Recall</th>
                <th className="py-3 px-4">F1-Score</th>
                <th className="py-3 px-4">Inference Latency</th>
                <th className="py-3 px-5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border/50 text-slate-200">
              {data.models.map((model) => (
                <tr key={model.key} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-4 px-5 font-bold text-white flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-blue-400" />
                    <span>{model.name}</span>
                  </td>
                  <td className="py-4 px-4 font-mono font-semibold text-emerald-400">
                    {model.accuracy.toFixed(2)}%
                  </td>
                  <td className="py-4 px-4 font-mono">{model.precision.toFixed(2)}%</td>
                  <td className="py-4 px-4 font-mono">{model.recall.toFixed(2)}%</td>
                  <td className="py-4 px-4 font-mono text-blue-300">{model.f1_score.toFixed(2)}%</td>
                  <td className="py-4 px-4 font-mono text-xs text-slate-400">
                    {model.latency_ms > 0 ? `${model.latency_ms.toFixed(4)} ms` : '< 1 ms'}
                  </td>
                  <td className="py-4 px-5 text-right">
                    {model.name === data.selected_production_model ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        Default
                      </span>
                    ) : (
                      <span className="text-[11px] font-medium text-slate-400">Alternative</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Grouped Bar Chart */}
      <div className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Metric Comparison Across Models</h3>
            <p className="text-xs text-slate-400">Accuracy, Precision, Recall, and F1-Score benchmarks</p>
          </div>
          <BarChart2 className="w-5 h-5 text-blue-400" />
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2d42" vertical={false} />
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} domain={[50, 100]} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111827',
                  borderColor: '#1f2d42',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey="Accuracy" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Precision" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Recall" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="F1-Score" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Confusion Matrix Interactive Visualizer */}
      <div className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-6 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-white">Empirical Confusion Matrix</h3>
            <p className="text-xs text-slate-400">
              Classification distribution of True Negatives, False Positives, False Negatives, and True Positives
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Select Model:</span>
            <select
              value={selectedModelKey}
              onChange={(e) => setSelectedModelKey(e.target.value)}
              className="bg-[#0b0f19] border border-surface-border rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              {data.models.map((m) => (
                <option key={m.key} value={m.key}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedModel.confusion_matrix ? (
          <div className="max-w-xl mx-auto space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {/* True Negative */}
              <div className="bg-[#0b0f19] border border-surface-border rounded-xl p-5 space-y-2 text-center">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                  True Negatives (TN)
                </span>
                <div className="text-3xl font-extrabold text-emerald-400 font-mono">
                  {selectedModel.confusion_matrix.true_negative.toLocaleString()}
                </div>
                <p className="text-[11px] text-slate-400">Actual Fake → Correctly Predicted Fake</p>
              </div>

              {/* False Positive */}
              <div className="bg-[#0b0f19] border border-surface-border rounded-xl p-5 space-y-2 text-center">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-rose-400 block">
                  False Positives (FP)
                </span>
                <div className="text-3xl font-extrabold text-rose-400 font-mono">
                  {selectedModel.confusion_matrix.false_positive.toLocaleString()}
                </div>
                <p className="text-[11px] text-slate-400">Actual Fake → Misclassified as Authentic</p>
              </div>

              {/* False Negative */}
              <div className="bg-[#0b0f19] border border-surface-border rounded-xl p-5 space-y-2 text-center">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-400 block">
                  False Negatives (FN)
                </span>
                <div className="text-3xl font-extrabold text-amber-400 font-mono">
                  {selectedModel.confusion_matrix.false_negative.toLocaleString()}
                </div>
                <p className="text-[11px] text-slate-400">Actual Authentic → Misclassified as Fake</p>
              </div>

              {/* True Positive */}
              <div className="bg-[#0b0f19] border border-surface-border rounded-xl p-5 space-y-2 text-center">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 block">
                  True Positives (TP)
                </span>
                <div className="text-3xl font-extrabold text-emerald-400 font-mono">
                  {selectedModel.confusion_matrix.true_positive.toLocaleString()}
                </div>
                <p className="text-[11px] text-slate-400">Actual Authentic → Correctly Predicted Authentic</p>
              </div>
            </div>

            <p className="text-center text-[11px] text-slate-400">
              Evaluated on {selectedModel.name} with consistent holdout test set (6,493 samples).
            </p>
          </div>
        ) : (
          <p className="text-center text-xs text-slate-400 py-8">
            Confusion matrix details currently unavailable for this model.
          </p>
        )}
      </div>
    </div>
  );
};

