import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock, Mail, ArrowRight, AlertCircle, Eye, EyeOff } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(
    searchParams.get('expired') ? 'Your session has expired. Please log in again.' : null
  );
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const userRole = await login(email.trim().toLowerCase(), password);
      // Role-based redirection:
      if (userRole === 'admin') {
        navigate('/admin');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-[#F8FAFF] px-4 py-12">
      <div className="w-full max-w-md rounded-2xl border border-[#CBD5E1] bg-white p-8 shadow-sm">
        <div className="text-center mb-8">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-tr from-[#1D4ED8] to-[#2563EB] text-white shadow-md mb-3">
            <ShieldCheck className="h-7 w-7 text-blue-200" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">Sign in to EvidenceRAG</h2>
          <p className="mt-1 text-xs text-[#475569]">Access pre-submission verification and audit history</p>
        </div>

        {error && (
          <div className="mb-5 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#0F172A] mb-1">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-[#475569]" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@evidencerag.com"
                className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 pl-9 pr-3 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-[#0F172A]">Password</label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-[11px] text-[#475569] hover:text-[#2563EB] flex items-center gap-1 cursor-pointer transition-colors"
              >
                {showPassword ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-[#475569]" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 pl-9 pr-10 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#2563EB] py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-[#1D4ED8] disabled:opacity-50 transition-colors cursor-pointer"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-[#475569]">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold text-[#2563EB] hover:underline">
            Register as applicant
          </Link>
        </div>
      </div>
    </div>
  );
};
