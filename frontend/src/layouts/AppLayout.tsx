import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

export const AppLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0b0f19] flex flex-col text-slate-100 selection:bg-blue-600 selection:text-white">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-surface-border bg-[#080c14] py-8 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} TruthLens AI. Production Fake News Detection & NLP Verification Platform.</p>
          <div className="flex items-center space-x-4">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              ML Engine 1.0.0 Active
            </span>
            <span className="text-slate-400">ISOT Verified Corpus</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

