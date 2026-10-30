import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, BarChart3, Search, History, BrainCircuit, User as UserIcon, LogOut, LogIn, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navLinks = [
    { name: 'Live Verify', path: '/verify', icon: CheckCircle2, authRequired: false, badge: '2.0' },
    { name: 'Analyze', path: '/analyze', icon: Search, authRequired: false },
    { name: 'Dashboard', path: '/dashboard', icon: BarChart3, authRequired: true },
    { name: 'History', path: '/history', icon: History, authRequired: true },
    { name: 'Model Insights', path: '/models', icon: BrainCircuit, authRequired: false },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0e1524]/90 backdrop-blur-md border-b border-surface-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 to-primary-500 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-all">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
              TruthLens
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                AI NLP
              </span>
            </span>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center space-x-1">
          {navLinks.map((link) => {
            if (link.authRequired && !isAuthenticated) return null;
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.name}</span>
                {link.badge && (
                  <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    {link.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User / Auth CTA */}
        <div className="flex items-center space-x-3">
          {isAuthenticated ? (
            <div className="flex items-center space-x-3">
              <Link
                to="/profile"
                className="flex items-center space-x-2 text-sm text-slate-300 hover:text-white bg-surface-card px-3 py-1.5 rounded-lg border border-surface-border"
              >
                <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-semibold">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email.charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:inline font-medium">{user?.full_name || user?.email.split('@')[0]}</span>
              </Link>
              <button
                onClick={handleLogout}
                title="Log out"
                className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors border border-transparent hover:border-rose-500/20"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link
                to="/login"
                className="flex items-center space-x-1 px-3.5 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                <span>Sign in</span>
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-600/25 transition-all"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

