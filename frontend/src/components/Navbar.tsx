import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, LogOut, User as UserIcon, LayoutDashboard, Database, HelpCircle } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-navy-900 to-brand-600 text-white shadow-md">
            <ShieldCheck className="h-6 w-6 text-brand-300" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-slate-900">Evidence<span className="text-brand-600">RAG</span></span>
              <span className="rounded bg-brand-50 px-1.5 py-0.5 text-[10px] font-bold text-brand-700 uppercase">AI Verification</span>
            </div>
            <p className="text-[10px] text-slate-500 hidden sm:block">Pre-Submission Application Audit & Explainable RAG</p>
          </div>
        </Link>

        {/* Navigation links & User actions */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              {isAdmin && (
                <Link
                  to="/admin"
                  className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800"
                >
                  Admin Panel
                </Link>
              )}

              {/* User profile dropdown/pill */}
              <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
                <Link to="/profile" className="flex items-center gap-2 text-left hover:opacity-80">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-brand-800 font-bold text-xs">
                    {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                  </div>
                  <div className="hidden sm:block">
                    <div className="text-xs font-semibold text-slate-800 truncate max-w-[120px]">{user.full_name || user.email}</div>
                    <div className="text-[10px] font-medium text-brand-600 capitalize">{user.role}</div>
                  </div>
                </Link>

                <button
                  onClick={logout}
                  title="Logout"
                  className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-rose-600"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="rounded-lg px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700"
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
