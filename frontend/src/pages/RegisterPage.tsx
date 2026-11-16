import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock, Mail, ArrowRight, AlertCircle, Eye, EyeOff, KeyRound, HelpCircle } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'student' | 'admin'>('student');
  const [password, setPassword] = useState('');
  const [adminCode, setAdminCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError('Password must be at least 6 characters in length.');
      return;
    }

    if (role === 'admin' && !adminCode.trim()) {
      setError('Administrator registration requires an Administrator Authorization Code.');
      return;
    }

    setLoading(true);
    try {
      const assignedRole = await register(
        email.trim().toLowerCase(),
        password,
        role,
        role === 'admin' ? adminCode.trim() : undefined
      );

      if (assignedRole === 'admin') {
        navigate('/admin');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Registration failed. Please check your credentials and try again.'
      );
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
          <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">Create an Account</h2>
          <p className="mt-1 text-xs text-[#475569]">
            Register as a scholarship applicant or administrator
          </p>
        </div>

        {error && (
          <div className="mb-5 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 1. Email Address */}
          <div>
            <label className="block text-xs font-semibold text-[#0F172A] mb-1">
              Email Address <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-[#475569]" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="applicant@example.com"
                className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 pl-9 pr-3 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
              />
            </div>
            <p className="mt-1 text-[11px] text-[#475569]">
              Used for account authentication and verification status notices.
            </p>
          </div>

          {/* 2. Account Role Dropdown */}
          <div>
            <label className="block text-xs font-semibold text-[#0F172A] mb-1">
              Account Role <span className="text-rose-500">*</span>
            </label>
            <select
              value={role}
              onChange={(e) => {
                setRole(e.target.value as 'student' | 'admin');
                setError(null);
              }}
              className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs font-medium text-[#0F172A] focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
            >
              <option value="student">Student / Scholarship Applicant</option>
              <option value="admin">Administrator (Verification Officer)</option>
            </select>
          </div>

          {/* Conditional Admin Authorization Code */}
          {role === 'admin' && (
            <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3.5 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-900">
                <KeyRound className="h-4 w-4 text-amber-600" />
                <span>Admin Authorization Code Required</span>
              </div>
              <p className="text-[11px] text-amber-800 leading-relaxed">
                To prevent unauthorized administrative access, official verification staff must supply an institution security key.
                <span className="block mt-1 font-mono text-[10px] text-amber-700 bg-amber-100/80 p-1 rounded">
                  Academic evaluation code: <code className="font-bold">AdminSecret@2026</code>
                </span>
              </p>
              <input
                type="password"
                required={role === 'admin'}
                value={adminCode}
                onChange={(e) => setAdminCode(e.target.value)}
                placeholder="Enter Administrator authorization key"
                className="w-full rounded-lg border border-amber-300 bg-white py-2 px-3 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
              />
            </div>
          )}

          {/* 3. Password with Show/Hide toggle */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-[#0F172A]">
                Password <span className="text-rose-500">*</span>
              </label>
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
                placeholder="Minimum 6 characters"
                className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 pl-9 pr-10 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
              />
            </div>
            <p className="mt-1 text-[11px] text-[#475569]">
              Passwords are securely hashed using bcrypt before persistence.
            </p>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#2563EB] py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-[#1D4ED8] disabled:opacity-50 transition-colors cursor-pointer"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-[#475569]">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-[#2563EB] hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};
