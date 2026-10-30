import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Globe,
  Search,
  Layers,
  FileCheck,
  Cpu,
  Quote,
  Sparkles,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-24 py-6">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto space-y-6 pt-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-sm">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multilingual Evidence-Based Verification</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
          Know What's True.{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-primary-500 to-indigo-300">
            Verify With Evidence.
          </span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Investigate news and factual claims using live sources, multilingual AI and transparent evidence.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            to="/verify"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2 transition-all"
          >
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span>Verify News Now</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="#how-it-works"
            className="w-full sm:w-auto px-7 py-3.5 rounded-xl font-medium text-slate-300 hover:text-white bg-surface-card hover:bg-slate-800 border border-surface-border transition-all flex items-center justify-center gap-2"
          >
            <span>How It Works</span>
          </a>
        </div>
      </section>

      {/* Performance & Quality Badges */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Traceable Evidence', value: '100%', desc: 'Zero hallucinated quotations' },
          { label: 'Multilingual Core', value: 'EN + HI', desc: 'English & Hindi (Devanagari)' },
          { label: 'Live Evidence Discovery', value: 'Multi-Tier', desc: 'SearXNG, GDELT & RSS' },
          { label: 'NLI Entailment Engine', value: 'Neural', desc: 'Premise-hypothesis inference' },
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

      {/* How It Works - 5-Stage Verification Pipeline */}
      <section id="how-it-works" className="space-y-12 scroll-mt-24">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Layers className="w-3.5 h-3.5" />
            <span>5-Stage Pipeline</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white">How TruthLens Verifies News</h2>
          <p className="text-slate-400 max-w-xl mx-auto text-sm">
            From raw news articles or URLs to an audited, evidence-backed verification report.
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-4">
          {[
            {
              step: '01',
              title: 'Claim Extraction',
              desc: 'Deconstructs news text into atomic, checkable factual claims using Ollama or linguistic analysis.',
              icon: Cpu,
            },
            {
              step: '02',
              title: 'Live Evidence Discovery',
              desc: 'Dispatches neutral and counter-queries across trusted news sources, RSS feeds, and web indexes.',
              icon: Search,
            },
            {
              step: '03',
              title: 'Retrieval & Filtering',
              desc: 'Fetches original publisher pages, filters ads, clusters syndicated wire duplicates, and verifies entity relevance.',
              icon: Globe,
            },
            {
              step: '04',
              title: 'NLI Verification',
              desc: 'Cross-checks claims against retrieved passages using cross-lingual Natural Language Inference (NLI).',
              icon: Quote,
            },
            {
              step: '05',
              title: 'Report Generation',
              desc: 'Synthesizes transparent verdicts (SUPPORTED, REFUTED, MIXED, UNVERIFIED) with plain-language explanations.',
              icon: FileCheck,
            },
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <div
                key={i}
                className="bg-surface-card border border-surface-border rounded-2xl p-5 relative flex flex-col justify-between hover:border-blue-500/30 transition-all space-y-4"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                    {item.step}
                  </span>
                  <Icon className="w-5 h-5 text-slate-400" />
                </div>
                <h3 className="text-base font-semibold text-white">{item.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Core Architectural Guarantees */}
      <section className="grid md:grid-cols-3 gap-8">
        <div className="bg-surface-card border border-surface-border rounded-2xl p-8 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white">Verbatim Source Quotes</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Every quote displayed in a verification report is matched directly against the publisher's extracted source text. No hallucinated citations or fabricated sources.
          </p>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-8 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
            <Layers className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white">Syndication Detection</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Detects wire agency reprints (PTI, Reuters, AP) so syndicated copies are never counted as multiple independent confirmations of the same claim.
          </p>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-8 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white">Multilingual Verification</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Seamlessly handles English, Hindi in Devanagari script, and code-mixed Hinglish claims, retrieving local and international reporting.
          </p>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="bg-gradient-to-r from-blue-900/40 via-indigo-950/40 to-slate-900 border border-blue-500/20 rounded-3xl p-10 sm:p-14 text-center space-y-6">
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white">Start Investigating News Today</h2>
        <p className="text-slate-300 max-w-xl mx-auto text-sm sm:text-base">
          Verify any news article as a guest immediately, or sign up for a free account to track your verification history and explore analytics.
        </p>
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/verify"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-500 shadow-xl shadow-blue-600/30 transition-all"
          >
            <span>Start Free Verification</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/register"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl font-medium text-slate-300 hover:text-white bg-surface-card hover:bg-slate-800 border border-surface-border transition-all"
          >
            <span>Create Account</span>
          </Link>
        </div>
      </section>
    </div>
  );
};
