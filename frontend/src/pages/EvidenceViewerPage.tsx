import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import {
  FileSearch,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  ShieldAlert,
  FileText,
  Sparkles,
  Eye,
  Download,
  Info
} from 'lucide-react';

interface EvidenceData {
  issue_id: number;
  verification_id: number;
  title: string;
  category: string;
  severity: string;
  document_id: number | null;
  document_name: string;
  page_number: number;
  evidence_snippet: string;
  expected_value?: string;
  actual_value?: string;
  explanation: string;
  suggested_correction: string;
  confidence_score: number;
  manual_review_recommended: boolean;
  rag_rule_id?: string;
  rag_source?: string;
  bbox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  is_exact_bbox: boolean;
  preview_url?: string;
}

export const EvidenceViewerPage: React.FC = () => {
  const { issueId } = useParams<{ issueId: string }>();
  const navigate = useNavigate();

  const [evidence, setEvidence] = useState<EvidenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvidence = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get(`/evidence/${issueId}`);
        setEvidence(res.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load issue evidence.');
      } finally {
        setLoading(false);
      }
    };
    if (issueId) {
      fetchEvidence();
    }
  }, [issueId]);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center text-xs text-[#475569]">
        <FileSearch className="h-6 w-6 animate-pulse text-[#2563EB] mr-2" />
        Pinpointing document page and bounding coordinates...
      </div>
    );
  }

  if (error || !evidence) {
    return (
      <div className="max-w-2xl mx-auto mt-12 rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center space-y-4">
        <AlertCircle className="mx-auto h-8 w-8 text-rose-600" />
        <h2 className="text-base font-bold text-rose-900">Evidence Not Available</h2>
        <p className="text-xs text-rose-700">{error || 'Could not locate evidence for this issue ID.'}</p>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:underline"
        >
          <ArrowLeft className="h-4 w-4" /> Return to Dashboard
        </Link>
      </div>
    );
  }

  const isCritical = evidence.severity.toLowerCase() === 'critical';
  const bbox = evidence.bbox || { x: 0.1, y: 0.2, width: 0.8, height: 0.08 };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Navigation & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1 rounded-lg border border-[#CBD5E1] bg-white px-3 py-1.5 text-xs font-semibold text-[#0F172A] hover:bg-slate-50 cursor-pointer transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Back
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                  isCritical ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                }`}
              >
                {evidence.severity} Issue
              </span>
              <span className="text-xs text-[#475569]">
                Issue #{evidence.issue_id} • Page {evidence.page_number}
              </span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-[#0F172A] mt-0.5">
              {evidence.title}
            </h1>
          </div>
        </div>

        {evidence.document_id && (
          <Link
            to={`/documents/${evidence.document_id}`}
            className="flex items-center gap-1.5 rounded-lg border border-[#CBD5E1] bg-white px-3.5 py-2 text-xs font-semibold text-[#0F172A] hover:bg-slate-50 cursor-pointer transition-colors"
          >
            <FileText className="h-4 w-4 text-[#2563EB]" />
            Full Document Details
          </Link>
        )}
      </div>

      {/* Main Evidence Layout: Document Preview with Bounding Box on Left, Evidence Card on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Visual Document Preview with Bounding Box Highlight Overlay */}
        <div className="lg:col-span-7 rounded-2xl border border-[#CBD5E1] bg-white p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2">
              <Eye className="h-4 w-4 text-[#2563EB]" />
              <span className="text-xs font-bold text-[#0F172A]">{evidence.document_name}</span>
              <span className="text-[11px] text-[#475569]">(Page {evidence.page_number})</span>
            </div>
            <span className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-mono text-[#2563EB]">
              {evidence.is_exact_bbox ? 'Exact OCR Bounding Box' : 'Document Region Highlight'}
            </span>
          </div>

          <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-[#F8FAFF] min-h-[480px] flex items-center justify-center">
            {evidence.preview_url ? (
              <div className="relative w-full h-[540px]">
                {/* Embed PDF/Image Preview */}
                <iframe
                  src={`${evidence.preview_url}#page=${evidence.page_number}`}
                  title="Document Preview"
                  className="w-full h-full rounded-lg"
                />

                {/* Highlight Overlay Bounding Box */}
                <div
                  className="absolute pointer-events-none rounded-sm border-2 border-rose-500 bg-rose-500/20 shadow-xs animate-pulse"
                  style={{
                    left: `${bbox.x * 100}%`,
                    top: `${bbox.y * 100}%`,
                    width: `${Math.max(15, bbox.width * 100)}%`,
                    height: `${Math.max(4, bbox.height * 100)}%`
                  }}
                >
                  <span className="absolute -top-5 left-0 rounded bg-rose-600 px-1.5 py-0.5 text-[9px] font-bold text-white shadow">
                    Flagged Area
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center p-8 text-xs text-[#475569]">
                <FileText className="mx-auto h-12 w-12 text-slate-300 mb-2" />
                Preview not available for this file type.
              </div>
            )}
          </div>

          <div className="flex items-center justify-between text-[11px] text-[#475569] pt-1">
            <span className="flex items-center gap-1">
              <Info className="h-3.5 w-3.5 text-blue-500" />
              OCR Bounding Coordinates: [{bbox.x}, {bbox.y}, {bbox.width}, {bbox.height}]
            </span>
            {evidence.preview_url && (
              <a
                href={evidence.preview_url}
                target="_blank"
                rel="noreferrer"
                className="text-[#2563EB] hover:underline font-semibold flex items-center gap-1"
              >
                Open Raw Document <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>

        {/* Right Column: Deep RAG Evidence Analysis & Actionable Fix */}
        <div className="lg:col-span-5 space-y-4">
          {/* Extracted Evidence Snippet Card */}
          <div className="rounded-2xl border border-[#CBD5E1] bg-white p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-[#0F172A] uppercase tracking-wider">
              Extracted Document Evidence
            </h3>

            <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5">
              <span className="text-[10px] font-semibold text-[#475569] uppercase block mb-1">
                Extracted Snippet from Page {evidence.page_number}:
              </span>
              <p className="font-mono text-xs text-[#0F172A] bg-white p-2.5 rounded-lg border border-slate-200 leading-relaxed">
                "{evidence.evidence_snippet || 'No specific snippet recognized'}"
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="rounded-lg border border-rose-100 bg-rose-50/50 p-2.5">
                <span className="text-[10px] font-semibold text-rose-800 uppercase block">
                  Actual Extracted Value:
                </span>
                <span className="font-mono text-xs font-bold text-rose-700 mt-0.5 block truncate">
                  {evidence.actual_value || 'Missing / Not Found'}
                </span>
              </div>
              <div className="rounded-lg border border-emerald-100 bg-emerald-50/50 p-2.5">
                <span className="text-[10px] font-semibold text-emerald-800 uppercase block">
                  Expected Benchmark:
                </span>
                <span className="font-mono text-xs font-bold text-emerald-700 mt-0.5 block truncate">
                  {evidence.expected_value || 'Valid Statutory Format'}
                </span>
              </div>
            </div>
          </div>

          {/* RAG Explainable Grounding Card */}
          <div className="rounded-2xl border border-blue-200 bg-gradient-to-tr from-blue-50/40 via-white to-purple-50/30 p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#2563EB]">
              <Sparkles className="h-4 w-4" />
              <span>RAG Statutory Grounding & Policy Citation</span>
            </div>

            <p className="text-xs text-[#0F172A] leading-relaxed">
              {evidence.explanation}
            </p>

            {evidence.rag_source && (
              <div className="rounded-xl border border-blue-100 bg-white p-3 text-[11px] text-[#475569]">
                <span className="font-semibold text-slate-700 block text-[10px] uppercase">
                  Regulatory Citation:
                </span>
                <div className="mt-0.5 font-medium text-[#0F172A]">{evidence.rag_source}</div>
                {evidence.rag_rule_id && (
                  <span className="inline-block mt-1 rounded bg-blue-100 px-1.5 py-0.5 text-[9px] font-mono font-bold text-[#2563EB]">
                    {evidence.rag_rule_id}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Recommended Action Card */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-5 shadow-sm space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-900">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Recommended Pre-Submission Fix</span>
            </div>
            <p className="text-xs text-emerald-950 leading-relaxed bg-white/90 p-3 rounded-xl border border-emerald-100">
              {evidence.suggested_correction}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
