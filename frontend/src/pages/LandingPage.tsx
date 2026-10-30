import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Cpu, Zap, Eye, CheckCircle2, ArrowRight, BarChart2, Layers, Lock } from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-24 py-6">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto space-y-6 pt-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-sm">
          <Cpu className="w-3.5 h-3.5" />
          <span>Production Natural Language Processing Engine</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
          Detect Misinformation with{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-primary-500 to-indigo-300">
            Explainable AI
          </span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
          TruthLens combines deterministic text preprocessing, high-dimensional TF-IDF feature extraction,
          and calibrated classifiers to evaluate news credibility in milliseconds.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            to="/verify"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2 transition-all"
          >
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span>Verify with Live AI (2.0)</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/analyze"
            className="w-full sm:w-auto px-7 py-3.5 rounded-xl font-medium text-slate-300 hover:text-white bg-surface-card hover:bg-slate-800 border border-surface-border transition-all flex items-center justify-center gap-2"
          >
            <span>Analyze (ML Classifier)</span>
          </Link>
        </div>
      </section>

      {/* Verified Performance Metrics */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Validated Accuracy', value: '97.71%', desc: 'Tested on ISOT corpus' },
          { label: 'Inference Latency', value: '< 1 ms', desc: 'Sub-millisecond prediction' },
          { label: 'Feature Space', value: '10,000', desc: 'N-Gram TF-IDF features' },
          { label: 'Explainable AI', value: '100%', desc: 'Directional token attribution' },
        ].map((stat, i) => (
          <div
            key={i}
            className="bg-surface-card/60 backdrop-blur border border-surface-border rounded-2xl p-6 text-center space-y-2 hover:border-blue-500/30 transition-colors"
          >
            <div className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">{stat.value}</div>
            <div className="text-sm font-semibold text-blue-400">{stat.label}</div>
            <div className="text-xs text-slate-400">{stat.desc}</div>
          </div>
        ))}
      </section>

      {/* How It Works */}
      <section className="space-y-12">
        <div className="text-center space-y-3">
          <h2 className="text-3xl font-bold tracking-tight text-white">How TruthLens Works</h2>
          <p className="text-slate-400 max-w-xl mx-auto text-sm">
            From raw news text or web URLs to interpretable credibility scores through an audited pipeline.
          </p>
        </div>

        <div className="grid md:grid-cols-4 gap-6">
          {[
            {
              step: '01',
              title: 'Ingestion & Safety',
              desc: 'Accepts raw text or URLs. Uses SSRF-resistant fetchers with strict timeout and private IP filtering.',
              icon: Lock,
            },
            {
              step: '02',
              title: 'NLP Preprocessing',
              desc: 'Cleans URLs, removes HTML artifacts, normalizes punctuation, and strips English stopwords deterministically.',
              icon: Layers,
            },
            {
              step: '03',
              title: 'TF-IDF Vectorization',
              desc: 'Maps text to a pre-fitted 10,000 unigram/bigram sublinear vocabulary without train/test data leakage.',
              icon: Zap,
            },
            {
              step: '04',
              title: 'Explainable Inference',
              desc: 'Calculates calibrated log-odds probability and extracts directional influential words with transparent explanations.',
              icon: Eye,
            },
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <div
                key={i}
                className="bg-surface-card border border-surface-border rounded-2xl p-6 relative flex flex-col justify-between hover:border-slate-600 transition-all"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                      {item.step}
                    </span>
                    <Icon className="w-5 h-5 text-slate-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{item.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Core Features */}
      <section className="grid md:grid-cols-3 gap-8">
        <div className="bg-surface-card border border-surface-border rounded-2xl p-8 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white">Calibrated Classifiers</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Trained and benchmarked on 32,000+ authentic news documents across Logistic Regression and Random Forest architectures.
          </p>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-8 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
            <Eye className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white">Explainable AI (XAI)</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Inspect the exact linguistic tokens that drove the prediction toward authentic journalism or fabricated claims.
          </p>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-8 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white">URL Web Scraper</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Paste any published news URL to automatically extract clean text, author, domain, and publication date with SSRF protection.
          </p>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="bg-gradient-to-r from-blue-900/40 via-indigo-950/40 to-slate-900 border border-blue-500/20 rounded-3xl p-10 sm:p-14 text-center space-y-6">
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white">Start Analyzing News Credibility Today</h2>
        <p className="text-slate-300 max-w-xl mx-auto text-sm sm:text-base">
          Sign up to track your analysis history, review longitudinal trends, and explore model performance metrics.
        </p>
        <div className="pt-2">
          <Link
            to="/register"
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-500 shadow-xl shadow-blue-600/30 transition-all"
          >
            <span>Create Free Account</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  );
};

