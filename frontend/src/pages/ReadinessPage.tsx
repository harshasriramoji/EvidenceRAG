import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import {
  Gauge,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ArrowRight,
  FileText,
  ShieldCheck,
  RefreshCw,
  Info
} from 'lucide-react';

interface ReadinessData {
  application_score: number;
  readiness_status: string;
  badge_color: string;
  total_documents: number;
  documents: Array<{
    document_id: number;
    document_name: string;
    category: string;
    overall_score: number;
    readiness_status: string;
    badge_color: string;
    breakdown: {
      completeness_score: number;
      validation_score: number;
      quality_score: number;
    };
    deductions: Array<{
      category: string;
      points: number;
      reason: string;
    }>;
  }>;
  overall_deductions: Array<{
    document: string;
    category: string;
    points: number;
    reason: string;
  }>;
  formula: string;
}

export const ReadinessPage: React.FC = () => {
  const [data, setData] = useState<ReadinessData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchReadiness = async () => {
    setLoading(true);
    try {
      const res = await api.get('/readiness');
      setData(res.data);
    } catch (err) {
      console.error('Error fetching readiness scores:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReadiness();
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center text-xs text-[#475569]">
        <RefreshCw className="h-6 w-6 animate-spin text-[#2563EB] mr-2" />
        Calculating statutory completeness and readiness scores...
      </div>
    );
  }

  const score = data?.application_score || 0;
  const isGood = score >= 80;
  const isMed = score >= 60 && score < 80;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Gauge className="h-6 w-6 text-[#2563EB]" />
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Document Readiness Score</h1>
          </div>
          <p className="mt-1 text-xs text-[#475569]">
            Transparent 0–100 pre-submission compliance audit measuring statutory completeness, visual scan quality, and defect absence.
          </p>
        </div>
        <button
          onClick={fetchReadiness}
          className="flex items-center gap-1.5 rounded-lg border border-[#CBD5E1] bg-white px-3.5 py-2 text-xs font-semibold text-[#0F172A] hover:bg-slate-50 cursor-pointer"
        >
          <RefreshCw className="h-3.5 w-3.5 text-[#475569]" /> Recalculate
        </button>
      </div>

      {/* Main Score Hero Card */}
      <div className="rounded-2xl border border-blue-200 bg-gradient-to-r from-blue-50/50 via-white to-purple-50/30 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            {/* Big Circular Metric */}
            <div className="relative flex h-28 w-28 items-center justify-center rounded-full border-4 border-[#2563EB]/20 bg-white shadow-inner">
              <div className="text-center">
                <span className="text-3xl font-extrabold text-[#0F172A]">{score}</span>
                <span className="block text-[10px] font-bold text-[#475569] uppercase">/ 100</span>
              </div>
            </div>

            <div>
              <span
                className={`inline-block rounded-full px-3 py-1 text-xs font-bold ${
                  isGood
                    ? 'bg-emerald-100 text-emerald-800'
                    : isMed
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-rose-100 text-rose-800'
                }`}
              >
                {data?.readiness_status}
              </span>
              <h2 className="text-lg font-bold text-[#0F172A] mt-1">Application Packet Audit Status</h2>
              <p className="text-xs text-[#475569] max-w-md mt-0.5 leading-relaxed">
                Evaluated across {data?.total_documents} uploaded certificate(s). A minimum threshold of 80/100 is recommended before final submission to scholarship portals.
              </p>
            </div>
          </div>

          <div className="text-right">
            <Link
              to="/verify/cross"
              className="inline-flex items-center gap-1.5 rounded-xl bg-[#2563EB] px-4 py-2.5 text-xs font-semibold text-white shadow hover:bg-[#1D4ED8]"
            >
              Run Full Verification <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>

        {/* Scoring Formula Explainer */}
        <div className="mt-6 pt-4 border-t border-blue-100 flex items-center gap-2 text-[11px] text-[#475569]">
          <Info className="h-4 w-4 text-[#2563EB] shrink-0" />
          <span><b>Transparent Formula:</b> 40% Mandatory Field Completeness + 40% Defect-Free Validation + 20% Scan Focus & DPI Quality.</span>
        </div>
      </div>

      {/* Per-Document Score Cards Grid */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-[#0F172A]">Individual Document Score Breakdown</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.documents && data.documents.length > 0 ? (
            data.documents.map((d) => (
              <div
                key={d.document_id}
                className="rounded-2xl border border-[#CBD5E1] bg-white p-5 shadow-xs space-y-3"
              >
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <div>
                    <h4 className="text-xs font-bold text-[#0F172A]">{d.document_name}</h4>
                    <span className="text-[10px] text-[#475569]">{d.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-extrabold text-[#2563EB]">{d.overall_score}</span>
                    <span className="text-[10px] text-[#475569]"> / 100</span>
                  </div>
                </div>

                {/* Breakdown Bars */}
                <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                  <div className="rounded-lg bg-slate-50 p-2 border border-slate-100">
                    <div className="text-slate-500">Completeness</div>
                    <div className="font-bold text-[#0F172A] text-xs">{d.breakdown.completeness_score}%</div>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-2 border border-slate-100">
                    <div className="text-slate-500">Validation</div>
                    <div className="font-bold text-[#0F172A] text-xs">{d.breakdown.validation_score}%</div>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-2 border border-slate-100">
                    <div className="text-slate-500">Scan Quality</div>
                    <div className="font-bold text-[#0F172A] text-xs">{d.breakdown.quality_score}%</div>
                  </div>
                </div>

                {/* Deductions if any */}
                {d.deductions && d.deductions.length > 0 ? (
                  <div className="rounded-lg bg-rose-50/60 p-2.5 border border-rose-100 space-y-1">
                    <span className="text-[10px] font-bold text-rose-900 block">Deductions Applied:</span>
                    {d.deductions.map((ded, i) => (
                      <div key={i} className="text-[10px] text-rose-800 flex items-start gap-1">
                        <span className="font-mono font-bold text-rose-700">-{ded.points}pts:</span>
                        <span>{ded.reason}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-[11px] text-emerald-700 flex items-center gap-1 font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                    Zero deductions! Certificate is compliant with all statutory criteria.
                  </div>
                )}

                <div className="pt-2 flex justify-end">
                  <Link
                    to={`/verify/single?docId=${d.document_id}`}
                    className="text-xs font-semibold text-[#2563EB] hover:underline flex items-center gap-1"
                  >
                    View Single Verification <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-xs text-[#475569] col-span-2 rounded-xl border border-[#CBD5E1] bg-white">
              No documents uploaded yet. Upload your credentials to generate readiness scores.
            </div>
          )}
        </div>
      </div>

      {/* Detailed Actionable Deductions Table */}
      {data?.overall_deductions && data.overall_deductions.length > 0 && (
        <div className="rounded-2xl border border-[#CBD5E1] bg-white p-5 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-[#0F172A]">All Deductions & Suggested Improvements</h3>
          <p className="text-xs text-[#475569]">
            Resolve the following items to reach 100% readiness prior to application submission.
          </p>

          <div className="divide-y divide-slate-100">
            {data.overall_deductions.map((ded, idx) => (
              <div key={idx} className="py-2.5 flex items-start justify-between gap-4 text-xs">
                <div>
                  <span className="font-semibold text-[#0F172A]">{ded.document}</span>
                  <div className="text-[11px] text-[#475569] mt-0.5">{ded.reason}</div>
                </div>
                <span className="rounded bg-rose-100 px-2 py-0.5 font-mono text-[10px] font-bold text-rose-800 shrink-0">
                  -{ded.points} pts
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
