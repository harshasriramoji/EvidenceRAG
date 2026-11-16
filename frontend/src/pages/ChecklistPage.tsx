import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import {
  ListChecks,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  Upload,
  FileText,
  ShieldCheck,
  RefreshCw,
  Plus
} from 'lucide-react';

interface ChecklistResponse {
  selected_scheme: {
    id: number;
    name: string;
    description: string;
    min_score: number;
  };
  available_schemes: Array<{
    id: number;
    name: string;
    description: string;
    min_score: number;
  }>;
  progress_percentage: number;
  total_required: number;
  satisfied_count: number;
  missing_count: number;
  checklist: Array<{
    category: string;
    is_uploaded: boolean;
    document_id: number | null;
    document_name: string | null;
    status: string;
    color: string;
    issue_count: number;
    action_needed: string | null;
  }>;
}

export const ChecklistPage: React.FC = () => {
  const [data, setData] = useState<ChecklistResponse | null>(null);
  const [selectedSchemeId, setSelectedSchemeId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchChecklist = async (schemeId?: number) => {
    setLoading(true);
    try {
      const url = schemeId ? `/checklist?scheme_id=${schemeId}` : '/checklist';
      const res = await api.get(url);
      setData(res.data);
      if (res.data?.selected_scheme && !selectedSchemeId) {
        setSelectedSchemeId(res.data.selected_scheme.id);
      }
    } catch (err) {
      console.error('Failed to load checklist:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChecklist();
  }, []);

  const handleSchemeChange = (id: number) => {
    setSelectedSchemeId(id);
    fetchChecklist(id);
  };

  if (loading && !data) {
    return (
      <div className="flex h-96 items-center justify-center text-xs text-[#475569]">
        <RefreshCw className="h-6 w-6 animate-spin text-[#2563EB] mr-2" />
        Evaluating scholarship application checklist...
      </div>
    );
  }

  const pct = data?.progress_percentage || 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ListChecks className="h-6 w-6 text-[#2563EB]" />
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
              Scholarship Application Readiness Checklist
            </h1>
          </div>
          <p className="mt-1 text-xs text-[#475569]">
            Verify that all mandatory credentials for your targeted scholarship program are uploaded, validated, and free of defects.
          </p>
        </div>

        {/* Scheme Selector Dropdown */}
        <div className="w-full sm:w-72">
          <label className="block text-[11px] font-semibold text-[#475569] uppercase mb-1">
            Target Scholarship Scheme:
          </label>
          <select
            value={selectedSchemeId || ''}
            onChange={(e) => handleSchemeChange(Number(e.target.value))}
            className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
          >
            {data?.available_schemes?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Progress Card */}
      <div className="rounded-2xl border border-blue-200 bg-white p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-bold text-[#0F172A]">{data?.selected_scheme.name}</h2>
            <p className="text-xs text-[#475569] mt-0.5">{data?.selected_scheme.description}</p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-extrabold text-[#2563EB]">{pct}%</span>
            <span className="text-xs text-[#475569] block">Requirements Met</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                pct === 100 ? 'bg-emerald-500' : pct >= 60 ? 'bg-[#2563EB]' : 'bg-amber-500'
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="flex justify-between text-[11px] text-[#475569]">
            <span>{data?.satisfied_count} of {data?.total_required} mandatory categories fulfilled</span>
            <span>{data?.missing_count} credential(s) missing</span>
          </div>
        </div>
      </div>

      {/* Checklist Items Table */}
      <div className="rounded-2xl border border-[#CBD5E1] bg-white p-5 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-[#0F172A]">Required Document Categories</h3>

        <div className="space-y-3">
          {data?.checklist.map((item, idx) => (
            <div
              key={idx}
              className={`rounded-xl border p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 transition-colors ${
                item.is_uploaded
                  ? 'border-slate-200 bg-white'
                  : 'border-dashed border-slate-300 bg-slate-50/70'
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg font-bold text-xs shrink-0 ${
                    item.color === 'emerald'
                      ? 'bg-emerald-100 text-emerald-700'
                      : item.color === 'rose'
                      ? 'bg-rose-100 text-rose-700'
                      : item.color === 'purple'
                      ? 'bg-purple-100 text-purple-700'
                      : item.color === 'amber'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {item.color === 'emerald' ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : item.color === 'rose' ? (
                    <XCircle className="h-4 w-4" />
                  ) : item.color === 'purple' ? (
                    <Clock className="h-4 w-4" />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#0F172A]">{item.category}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                        item.color === 'emerald'
                          ? 'bg-emerald-100 text-emerald-800'
                          : item.color === 'rose'
                          ? 'bg-rose-100 text-rose-800'
                          : item.color === 'purple'
                          ? 'bg-purple-100 text-purple-800'
                          : item.color === 'amber'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>

                  {item.is_uploaded ? (
                    <div className="text-[11px] text-[#475569] mt-0.5">
                      Attached: <span className="font-semibold text-slate-800">{item.document_name}</span>
                      {item.issue_count > 0 && (
                        <span className="text-rose-600 font-medium ml-2">
                          • {item.issue_count} issue(s) flagged
                        </span>
                      )}
                    </div>
                  ) : (
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Not yet uploaded. Required for statutory scholarship consideration.
                    </div>
                  )}

                  {item.action_needed && (
                    <div className="text-[11px] text-amber-900 bg-amber-50 border border-amber-200 rounded p-1.5 mt-2 max-w-xl">
                      <b>Action:</b> {item.action_needed}
                    </div>
                  )}
                </div>
              </div>

              <div className="shrink-0 self-end sm:self-center">
                {item.is_uploaded && item.document_id ? (
                  <Link
                    to={`/verify/single?docId=${item.document_id}`}
                    className="flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:underline"
                  >
                    View Verification <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                ) : (
                  <Link
                    to="/upload"
                    className="flex items-center gap-1.5 rounded-lg bg-[#2563EB] px-3.5 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-[#1D4ED8]"
                  >
                    <Upload className="h-3.5 w-3.5" /> Upload {item.category}
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
