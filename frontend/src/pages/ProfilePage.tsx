import React from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Shield, Calendar, LogOut, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Account Profile</h1>
        <p className="text-sm text-slate-400">Manage your TruthLens account credentials and preferences</p>
      </div>

      <div className="bg-surface-card border border-surface-border rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        <div className="flex items-center gap-4 pb-6 border-b border-surface-border">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-700 to-primary-500 text-white flex items-center justify-center text-2xl font-bold shadow-lg shadow-blue-600/20">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{user?.full_name || 'TruthLens User'}</h2>
            <p className="text-xs text-slate-400 mt-0.5">{user?.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Shield className="w-3 h-3" />
                {user?.is_superuser ? 'Administrator' : 'Standard Analyst'}
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" />
                Verified
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#0b0f19] border border-surface-border text-sm">
            <div className="flex items-center gap-3 text-slate-400">
              <Mail className="w-4 h-4 text-slate-400" />
              <span>Email</span>
            </div>
            <span className="font-mono text-white text-xs">{user?.email}</span>
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#0b0f19] border border-surface-border text-sm">
            <div className="flex items-center gap-3 text-slate-400">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span>Member Since</span>
            </div>
            <span className="text-xs text-slate-300">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Active Member'}
            </span>
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#0b0f19] border border-surface-border text-sm">
            <div className="flex items-center gap-3 text-slate-400">
              <Shield className="w-4 h-4 text-slate-400" />
              <span>Account Status</span>
            </div>
            <span className="text-xs font-semibold text-emerald-400">Active</span>
          </div>
        </div>

        <div className="pt-4 border-t border-surface-border flex justify-end">
          <button
            onClick={handleLogout}
            className="px-5 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 text-xs font-semibold transition-all flex items-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign out of TruthLens</span>
          </button>
        </div>
      </div>
    </div>
  );
};

