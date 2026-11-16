import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import {
  FileText,
  FileCheck,
  Files,
  Upload,
  AlertTriangle,
  XCircle,
  Eye,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  Activity,
  Plus
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis
} from 'recharts';

export const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [docsRes, histRes] = await Promise.all([
          api.get('/documents'),
          api.get('/verify/history')
        ]);
        setDocuments(docsRes.data);
        setHistory(histRes.data);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Compute metrics from real database results
  const totalDocs = documents.length;
  const verifiedCount = history.length;
  const passedCount = history.filter((h) => h.overall_status === 'Passed').length;
  const warningsCount = history.filter((h) => h.overall_status === 'Passed with Warnings').length;
  const correctionCount = history.filter((h) => h.overall_status === 'Needs Correction').length;
  const reviewCount = history.filter((h) => h.overall_status === 'Manual Review Required').length;

  const statusDistribution = [
    { name: 'Passed', value: passedCount, color: '#10B981' },
    { name: 'Warnings', value: warningsCount, color: '#F59E0B' },
    { name: 'Needs Correction', value: correctionCount, color: '#EF4444' },
    { name: 'Manual Review', value: reviewCount, color: '#6366F1' },
  ].filter((d) => d.value > 0);

  const totalIssuesIdentified = history.reduce((acc, h) => acc + (h.total_issues || 0), 0);
  const totalCriticalIssues = history.reduce((acc, h) => acc + (h.critical_issues || 0), 0);

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="rounded-2xl border border-blue-200 bg-gradient-to-r from-[#1D4ED8] via-[#2563EB] to-[#7C3AED] p-6 text-white shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="rounded bg-white/20 px-2 py-0.5 text-[10px] font-semibold text-white uppercase tracking-wider">
            Applicant Workspace
          </span>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">Pre-Submission Verification Dashboard</h1>
          <p className="mt-1 text-xs text-blue-100">
            Audit scholarship credentials, cross-reference data across certificates, and resolve compliance issues.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/upload"
            className="flex items-center gap-1.5 rounded-lg bg-white px-4 py-2 text-xs font-semibold text-[#1D4ED8] shadow hover:bg-blue-50 transition-colors"
          >
            <Upload className="h-4 w-4" />
            Upload Document
          </Link>
          <Link
            to="/verify/cross"
            className="flex items-center gap-1.5 rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-xs font-semibold text-white hover:bg-white/20 transition-colors"
          >
            <Files className="h-4 w-4 text-white" />
            Cross-Verify
          </Link>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Total Uploads</span>
            <FileText className="h-4 w-4 text-slate-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{totalDocs}</div>
          <div className="mt-1 text-[11px] text-slate-500">In student repository</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Verified Audits</span>
            <Activity className="h-4 w-4 text-brand-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-brand-700">{verifiedCount}</div>
          <div className="mt-1 text-[11px] text-slate-500">Completed checks</div>
        </div>

        <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-4 shadow-sm">
          <div className="flex items-center justify-between text-emerald-800 text-xs font-medium">
            <span>Passed Clean</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-700">{passedCount}</div>
          <div className="mt-1 text-[11px] text-emerald-600">Zero defects found</div>
        </div>

        <div className="rounded-xl border border-amber-100 bg-amber-50/40 p-4 shadow-sm">
          <div className="flex items-center justify-between text-amber-800 text-xs font-medium">
            <span>Warnings</span>
            <AlertTriangle className="h-4 w-4 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-700">{warningsCount}</div>
          <div className="mt-1 text-[11px] text-amber-600">Minor issues</div>
        </div>

        <div className="rounded-xl border border-rose-100 bg-rose-50/40 p-4 shadow-sm">
          <div className="flex items-center justify-between text-rose-800 text-xs font-medium">
            <span>Needs Correction</span>
            <XCircle className="h-4 w-4 text-rose-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-700">{correctionCount}</div>
          <div className="mt-1 text-[11px] text-rose-600">Must fix before submit</div>
        </div>

        <div className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-4 shadow-sm">
          <div className="flex items-center justify-between text-indigo-800 text-xs font-medium">
            <span>Manual Review</span>
            <Eye className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-indigo-700">{reviewCount}</div>
          <div className="mt-1 text-[11px] text-indigo-600">Recommended reviews</div>
        </div>
      </div>

      {/* Charts & Status Visuals */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Verification Status Distribution */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-1">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Audit Status Distribution</h3>
          <p className="text-xs text-slate-500 mb-4">Overall outcomes of submitted verification batches</p>

          {statusDistribution.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusDistribution}
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {statusDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-xs text-slate-400">
              No verification runs yet. Run Mode A or Mode B to view charts.
            </div>
          )}

          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            {statusDistribution.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-slate-600 truncate">{item.name}:</span>
                <span className="font-semibold text-slate-900">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Mode Launchpad */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Verification Modes & Actions</h3>
          <p className="text-xs text-slate-500 mb-4">Execute single-document audits or multi-document cross-matching</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 hover:border-[#2563EB]/50 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <FileCheck className="h-5 w-5 text-emerald-600" />
                <span className="font-semibold text-xs text-[#0F172A]">Mode A: Single Document Audit</span>
              </div>
              <p className="text-xs text-[#475569] mb-4">
                Select any uploaded document to independently detect missing fields, invalid dates, blur, or expired validity.
              </p>
              <Link
                to="/verify/single"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2563EB] hover:text-[#1D4ED8]"
              >
                Launch Single Verifier <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 hover:border-[#2563EB]/50 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <Files className="h-5 w-5 text-[#2563EB]" />
                <span className="font-semibold text-xs text-[#0F172A]">Mode B: Cross-Document Verification</span>
              </div>
              <p className="text-xs text-[#475569] mb-4">
                Compare 2+ documents simultaneously to detect name, DOB, address, or income discrepancies.
              </p>
              <Link
                to="/verify/cross"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2563EB] hover:text-[#1D4ED8]"
              >
                Launch Cross-Verifier <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Uploaded Documents Table */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Your Uploaded Documents</h3>
            <p className="text-xs text-slate-500">Manage credentials and run instant verification</p>
          </div>
          <Link
            to="/upload"
            className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <Plus className="h-3.5 w-3.5" /> Add Document
          </Link>
        </div>

        {documents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-y border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">File Name</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Quality Score</th>
                  <th className="py-2.5 px-3">Scan Health</th>
                  <th className="py-2.5 px-3">Uploaded On</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.slice(0, 8).map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80">
                    <td className="py-2.5 px-3 font-medium text-slate-900 flex items-center gap-2">
                      <FileText className="h-4 w-4 text-brand-600 shrink-0" />
                      <span className="truncate max-w-[200px]">{doc.original_filename}</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">{doc.category}</td>
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-1.5">
                        <div className="h-1.5 w-16 bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              doc.quality_score >= 0.8
                                ? 'bg-emerald-500'
                                : doc.quality_score >= 0.6
                                ? 'bg-amber-500'
                                : 'bg-rose-500'
                            }`}
                            style={{ width: `${Math.round((doc.quality_score || 0.8) * 100)}%` }}
                          />
                        </div>
                        <span className="text-[11px] font-semibold text-slate-700">
                          {Math.round((doc.quality_score || 0.8) * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      {doc.is_blurry ? (
                        <span className="rounded bg-rose-50 px-2 py-0.5 text-[10px] font-semibold text-rose-700 border border-rose-200">
                          Blurry
                        </span>
                      ) : doc.is_low_res ? (
                        <span className="rounded bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700 border border-amber-200">
                          Low Res
                        </span>
                      ) : (
                        <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                          Sharp Scan
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="rounded px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                        >
                          Details
                        </Link>
                        <button
                          onClick={() => navigate(`/verify/single?docId=${doc.id}`)}
                          className="rounded bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 hover:bg-brand-100 transition-colors"
                        >
                          Verify (Mode A)
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-xs text-slate-500">
            <Upload className="mx-auto h-8 w-8 text-slate-300 mb-2" />
            <p className="font-medium text-slate-700">No documents uploaded yet.</p>
            <p className="mt-1">Upload your scholarship credentials (PDF, JPG, PNG) to begin verification.</p>
            <Link
              to="/upload"
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow hover:bg-brand-700"
            >
              Upload Document
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
