import React from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Mail, Shield, Calendar, LogOut } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">User Profile</h1>
        <p className="mt-1 text-xs text-slate-500">
          Manage your account credentials and system authorization.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
        <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-brand-600 to-navy-900 text-white font-bold text-2xl shadow-sm">
            {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">{user.full_name || 'Scholarship Applicant'}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700 capitalize">
                {user.role}
              </span>
              <span className="text-xs text-slate-500">ID #{user.id}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <div className="flex items-center gap-2 text-slate-500 mb-1">
              <Mail className="h-4 w-4" />
              <span>Registered Email</span>
            </div>
            <div className="font-semibold text-slate-900 text-sm">{user.email}</div>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <div className="flex items-center gap-2 text-slate-500 mb-1">
              <Shield className="h-4 w-4" />
              <span>System Role</span>
            </div>
            <div className="font-semibold text-slate-900 text-sm capitalize">{user.role} Access</div>
          </div>
        </div>

        <div className="border-t border-slate-100 pt-4 flex justify-between items-center">
          <span className="text-xs text-slate-400">EvidenceRAG 2.0 Security Isolation</span>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};
