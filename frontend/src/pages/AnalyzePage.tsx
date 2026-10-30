import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Search,
  Globe,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Clock,
  Sparkles,
  Layers,
  ArrowRight,
  Info,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';
import { analysisService } from '../services/api';
import { AnalysisResponse } from '../types';

export const AnalyzePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const resultIdParam = searchParams.get('resultId');

  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [selectedModel, setSelectedModel] = useState('logistic_regression');
  const [activeTab, setActiveTab] = useState<'text' | 'url'>('text');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AnalysisResponse | null>(null);

  // If resultId is provided in URL query, fetch saved report
  useEffect(() => {
    if (resultIdParam) {
      const fetchSavedReport = async () => {
        setLoading(true);
        try {
          const data = await analysisService.getAnalysis(parseInt(resultIdParam));
          setResult(data);
          if (data.article) {
            setTitle(data.article.title || '');
            setText(data.article.content || '');
            if (data.article.url) {
              setUrl(data.article.url);
              setActiveTab('url');
            }
          }
        } catch (err: any) {
          setError(err.response?.data?.detail || 'Failed to load analysis report.');
        } finally {
          setLoading(false);
        }
      };
      fetchSavedReport();
    }
  }, [resultIdParam]);

  const loadPreset = (type: 'real' | 'fake') => {
    setError('');
    setActiveTab('text');
    if (type === 'real') {
      setTitle('WASHINGTON (Reuters) - U.S. Federal Reserve leaves benchmark rate steady');
      setText(
        'WASHINGTON (Reuters) - The Federal Reserve held interest rates unchanged on Wednesday and signaled borrowing costs are likely to stay where they are for the foreseeable future, pointing to ongoing labor market strength and moderate economic expansion.'
      );
    } else {
      setTitle('SHOCKING DISCOVERY: Secret Alien Pyramids Found Hidden in Antarctica!');
      setText(
        'Whistleblower leaks classified space agency documents proving ancient extraterrestrial pyramids buried beneath the ice were kept secret from the public for over fifty years to conceal advanced alien technology.'
      );
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (activeTab === 'url' && !url.trim()) {
      setError('Please provide a valid web article URL.');
      return;
    }

    if (activeTab === 'text' && !title.trim() && !text.trim()) {
      setError('Please provide either a headline or news article text.');
      return;
    }

    setLoading(true);

    try {
      const payload: any = {
        model_name: selectedModel,
      };

      if (activeTab === 'url') {
        payload.url = url.trim();
        if (title.trim()) payload.title = title.trim();
        if (text.trim()) payload.text = text.trim();
      } else {
        payload.title = title.trim();
        payload.text = text.trim();
      }

      const res = await analysisService.analyze(payload);
      setResult(res);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Analysis failed. Please check inputs and try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Title */}
      <div className="space-y-2 text-center sm:text-left">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Evaluate Article Credibility</h1>
        <p className="text-sm text-slate-400">
          Submit raw news text or a direct article link to evaluate statistical authenticity markers.
        </p>
      </div>

      {/* Preset Quick Fill */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-xs text-slate-400 flex items-center gap-1 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          Test Sample:
        </span>
        <button
          type="button"
          onClick={() => loadPreset('real')}
          className="text-xs px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all font-medium"
        >
          ✓ Sample Authentic News (Reuters)
        </button>
        <button
          type="button"
          onClick={() => loadPreset('fake')}
          className="text-xs px-3 py-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 transition-all font-medium"
        >
          ✗ Sample Fabricated Tabloid
        </button>
      </div>

      {/* Form Container */}
      <div className="bg-surface-card border border-surface-border rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        {/* Tab Toggle */}
        <div className="flex p-1 bg-[#0b0f19] rounded-xl border border-surface-border w-full sm:w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('text')}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'text'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Text / Headline</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('url')}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'url'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Globe className="w-4 h-4" />
            <span>URL Extractor</span>
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold block">Validation Error</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleAnalyze} className="space-y-5">
          {activeTab === 'url' && (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-blue-400" />
                Article URL
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.reuters.com/world/article-slug..."
                className="w-full bg-[#0b0f19] border border-surface-border rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
              <p className="text-[11px] text-slate-400">
                Safe SSRF-protected extraction using Trafilatura parser (max 10s timeout, public hostnames only).
              </p>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-400" />
              Article Headline
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. As U.S. budget fight looms, lawmakers flip fiscal script"
              className="w-full bg-[#0b0f19] border border-surface-border rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              News Article Content
            </label>
            <textarea
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste complete news body here for deeper linguistic analysis..."
              className="w-full bg-[#0b0f19] border border-surface-border rounded-xl p-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors resize-y leading-relaxed"
            />
          </div>

          {/* Model Selection */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2 border-t border-surface-border">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-blue-400" />
                Select Classification Engine
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-[#0b0f19] border border-surface-border rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="logistic_regression">Logistic Regression (Recommended - 0.08ms, Calibrated XAI)</option>
                <option value="random_forest">Random Forest (Ensemble Trees - 200 estimators)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-7 py-3 rounded-xl font-semibold text-sm text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Evaluating text...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Run Credibility Analysis</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Analysis Result View */}
      {result && (
        <div className="bg-surface-card border border-surface-border rounded-2xl p-6 sm:p-8 space-y-8 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-300">
          {/* Header result badge */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-surface-border">
            <div className="flex items-center gap-3">
              <div
                className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                  result.prediction === 'REAL'
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                }`}
              >
                {result.prediction === 'REAL' ? (
                  <ShieldCheck className="w-8 h-8" />
                ) : (
                  <ShieldAlert className="w-8 h-8" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-2xl font-extrabold tracking-tight ${
                      result.prediction === 'REAL' ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {result.label}
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {result.prediction}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Evaluated using <strong className="text-slate-200">{result.model_name}</strong> in{' '}
                  <strong className="text-slate-200">{result.processing_time_ms} ms</strong>
                </p>
              </div>
            </div>

            <div className="bg-[#0b0f19] border border-surface-border rounded-xl px-5 py-3 text-right">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                Model Confidence
              </span>
              <span className="text-2xl font-mono font-extrabold text-white">
                {(result.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Probabilities Meter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-rose-400">
                Fabricated Probability: {(result.probabilities.fake * 100).toFixed(1)}%
              </span>
              <span className="text-emerald-400">
                Authentic Probability: {(result.probabilities.real * 100).toFixed(1)}%
              </span>
            </div>
            <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden flex">
              <div
                style={{ width: `${result.probabilities.fake * 100}%` }}
                className="bg-rose-500 h-full transition-all duration-500"
              />
              <div
                style={{ width: `${result.probabilities.real * 100}%` }}
                className="bg-emerald-500 h-full transition-all duration-500"
              />
            </div>
          </div>

          {/* Explainable AI (XAI) Attribution Grid */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <h3 className="text-base font-bold text-white">Explainable AI Feature Attribution</h3>
            </div>

            <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-500/20 text-xs text-slate-300 leading-relaxed">
              {result.explanation.summary}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Fake indicators */}
              <div className="bg-[#0b0f19] border border-surface-border rounded-xl p-4 space-y-3">
                <span className="text-xs font-bold text-rose-400 uppercase tracking-wider block">
                  Top Tokens Driving Fabrication Verdict
                </span>
                {result.explanation.top_fake_indicators.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No strong negative tokens detected.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {result.explanation.top_fake_indicators.map((ind, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20"
                      >
                        <span>{ind.word}</span>
                        <span className="text-[10px] text-rose-400/80">({ind.importance.toFixed(3)})</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Real indicators */}
              <div className="bg-[#0b0f19] border border-surface-border rounded-xl p-4 space-y-3">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">
                  Top Tokens Driving Authentic Verdict
                </span>
                {result.explanation.top_real_indicators.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No strong positive tokens detected.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {result.explanation.top_real_indicators.map((ind, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                      >
                        <span>{ind.word}</span>
                        <span className="text-[10px] text-emerald-400/80">({ind.importance.toFixed(3)})</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Important Scientific Disclaimer */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-3 text-xs text-amber-300/90 leading-relaxed">
            <Info className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
            <div>
              <strong className="block text-amber-300 font-semibold mb-0.5">Scientific & Ethical Advisory</strong>
              {result.disclaimer} TruthLens classifies documents based on linguistic style, vocabulary distribution, and
              journalistic attribution patterns learned from historical datasets. A classification of "Likely Fake" is an
              algorithmic prediction, not definitive proof of factual inaccuracy.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

