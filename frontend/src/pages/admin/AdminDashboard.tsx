import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../api/client';
import { StatusBadge } from '../../components/StatusBadge';
import {
  Users,
  FileText,
  Activity,
  ShieldAlert,
  Settings,
  Cpu,
  TrendingUp,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Eye,
  BookOpen
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export const AdminDashboard: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [metrics, setMetrics] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        const [dashRes, metricsRes] = await Promise.all([
          api.get('/admin/dashboard'),
          api.get('/admin/metrics').catch(() => ({ data: null }))
        ]);
        setData(dashRes.data);
        setMetrics(metricsRes.data);
      } catch (err) {
        console.error('Error fetching admin dashboard:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAdminData();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-400">Loading administrator dashboard...</div>;
  }

  const chartData = [
    { name: 'Passed', count: data?.passed_documents || 0, fill: '#10B981' },
    { name: 'Warnings', count: data?.warning_cases || 0, fill: '#F59E0B' },
    { name: 'Needs Fix', count: data?.correction_cases || 0, fill: '#EF4444' },
    { name: 'Review Needed', count: data?.manual_review_queue || 0, fill: '#6366F1' },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="rounded-2xl border border-slate-200 bg-slate-900 p-6 text-white shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-amber-400/20 px-2 py-0.5 text-[10px] font-bold text-amber-300 uppercase tracking-wider">
              System Administration
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Admin Control Panel & Verification Queue</h1>
          <p className="mt-1 text-xs text-slate-400">
            Monitor system-wide application verifications, audit flagged compliance cases, and manage verification rules.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link
            to="/admin/reviews"
            className="flex items-center gap-1.5 rounded-lg bg-rose-600 px-3.5 py-2 text-xs font-semibold text-white shadow hover:bg-rose-500 transition-colors"
          >
            <ShieldAlert className="h-4 w-4" />
            Reviews ({data?.pending_issues_review || 0})
          </Link>
          <Link
            to="/admin/knowledge-base"
            className="flex items-center gap-1.5 rounded-lg border border-purple-500/40 bg-purple-950/60 px-3.5 py-2 text-xs font-semibold text-purple-200 hover:bg-purple-900 transition-colors"
          >
            <BookOpen className="h-4 w-4 text-purple-300" />
            RAG Knowledge Base
          </Link>
          <Link
            to="/admin/rules"
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors"
          >
            <Settings className="h-4 w-4" />
            Rules
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Total Registered Users</span>
            <Users className="h-4 w-4 text-slate-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{data?.total_users || 0}</div>
          <Link to="/admin/users" className="mt-1 text-[11px] text-brand-600 font-medium hover:underline block">
            Manage Users →
          </Link>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Documents Ingested</span>
            <FileText className="h-4 w-4 text-slate-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{data?.total_documents || 0}</div>
          <div className="mt-1 text-[11px] text-slate-500">Across all categories</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Total Verification Audits</span>
            <Activity className="h-4 w-4 text-brand-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-brand-700">{data?.total_verifications || 0}</div>
          <div className="mt-1 text-[11px] text-slate-500">Mode A & Mode B runs</div>
        </div>

        <div className="rounded-xl border border-rose-200 bg-rose-50/40 p-4 shadow-sm">
          <div className="flex items-center justify-between text-rose-800 text-xs font-medium">
            <span>Flagged Review Queue</span>
            <ShieldAlert className="h-4 w-4 text-rose-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-700">{data?.pending_issues_review || 0}</div>
          <Link to="/admin/reviews" className="mt-1 text-[11px] text-rose-700 font-semibold hover:underline block">
            Review Queue →
          </Link>
        </div>
      </div>

      {/* Analytics & Machine Learning Performance */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Verification Status Breakdown */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-1">System-Wide Verification Outcomes</h3>
          <p className="text-xs text-slate-500 mb-4">Total audits categorized by automated evaluation status</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" fontSize={11} stroke="#64748B" />
                <YAxis fontSize={11} stroke="#64748B" />
                <Tooltip />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Machine Learning Model Performance */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              <Cpu className="h-4 w-4 text-brand-600" />
              Empirical ML Model Performance
            </h3>
            <span className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-brand-700">
              Scikit-Learn TF-IDF
            </span>
          </div>
          <p className="text-xs text-slate-500 mb-4">Evaluated on 125 synthetic document benchmark test split</p>

          {metrics ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
                  <span className="text-[10px] font-medium text-slate-500 uppercase">Accuracy</span>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {Math.round(metrics.accuracy * 100)}%
                  </div>
                </div>
                <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
                  <span className="text-[10px] font-medium text-slate-500 uppercase">Precision</span>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {Math.round(metrics.precision * 100)}%
                  </div>
                </div>
                <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
                  <span className="text-[10px] font-medium text-slate-500 uppercase">Recall</span>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {Math.round(metrics.recall * 100)}%
                  </div>
                </div>
                <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
                  <span className="text-[10px] font-medium text-slate-500 uppercase">F1-Score</span>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {Math.round(metrics.f1_score * 100)}%
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-700 border border-slate-100">
                <div className="font-semibold text-slate-900 mb-1">Evaluated Document Classes:</div>
                <div className="flex flex-wrap gap-1">
                  {metrics.classes?.map((c: string) => (
                    <span key={c} className="rounded bg-white border border-slate-200 px-2 py-0.5 text-[10px] text-slate-700">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-400">
              Evaluation metrics pending. Run train_classifier.py to view stats.
            </div>
          )}
        </div>
      </div>

      {/* Recent System Verification Activity */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-1">Recent Verification Audit Stream</h3>
        <p className="text-xs text-slate-500 mb-4">Latest pre-submission checks across all registered students</p>

        {data?.recent_activity && data.recent_activity.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-y border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Audit ID</th>
                  <th className="py-2.5 px-3">Applicant Email</th>
                  <th className="py-2.5 px-3">Mode</th>
                  <th className="py-2.5 px-3">Overall Status</th>
                  <th className="py-2.5 px-3">Total Issues</th>
                  <th className="py-2.5 px-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.recent_activity.map((act: any) => (
                  <tr key={act.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-semibold text-slate-900">#{act.id}</td>
                    <td className="py-2.5 px-3 text-slate-700">{act.user_email}</td>
                    <td className="py-2.5 px-3 text-slate-600 capitalize">{act.mode}</td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={act.overall_status} size="sm" />
                    </td>
                    <td className="py-2.5 px-3 text-slate-700 font-medium">{act.total_issues}</td>
                    <td className="py-2.5 px-3 text-slate-500">
                      {new Date(act.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 text-center text-xs text-slate-400">No activity logged yet.</div>
        )}
      </div>
    </div>
  );
};
