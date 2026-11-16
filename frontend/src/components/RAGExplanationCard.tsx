import React from 'react';
import { ShieldCheck, BookOpen, AlertOctagon, HelpCircle, ArrowRight } from 'lucide-react';

export interface IssueItem {
  id?: number;
  title: string;
  category: string;
  severity: string;
  document_name?: string;
  page_number?: number;
  evidence_snippet?: string;
  expected_value?: string;
  actual_value?: string;
  explanation: string;
  suggested_correction: string;
  confidence_score: number;
  manual_review_recommended?: boolean;
  rag_rule_id?: string;
  rag_source?: string;
}

interface RAGExplanationCardProps {
  issue: IssueItem;
  index?: number;
}

export const RAGExplanationCard: React.FC<RAGExplanationCardProps> = ({ issue, index }) => {
  const isCritical = issue.severity === 'critical';
  const isHigh = issue.severity === 'high';

  const borderClass = isCritical
    ? 'border-rose-200 bg-rose-50/30'
    : isHigh
    ? 'border-amber-200 bg-amber-50/20'
    : 'border-slate-200 bg-white';

  const badgeColor = isCritical
    ? 'bg-rose-100 text-rose-800'
    : isHigh
    ? 'bg-amber-100 text-amber-800'
    : 'bg-blue-100 text-blue-800';

  return (
    <div className={`rounded-xl border p-5 shadow-sm transition-all hover:shadow-md ${borderClass}`}>
      <div className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          {index !== undefined && (
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">
              {index}
            </span>
          )}
          <h4 className="font-semibold text-slate-900">{issue.title}</h4>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${badgeColor}`}>
            {issue.severity}
          </span>
          {issue.manual_review_recommended && (
            <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-800">
              Review Recommended
            </span>
          )}
        </div>
      </div>

      {/* Document & Evidence grid */}
      <div className="mt-3 grid grid-cols-1 gap-2 text-xs md:grid-cols-2">
        {issue.document_name && (
          <div className="text-slate-600">
            <span className="font-medium text-slate-900">Document: </span>
            {issue.document_name}
          </div>
        )}
        {issue.expected_value && (
          <div className="text-slate-600">
            <span className="font-medium text-slate-900">Expected: </span>
            <span className="text-emerald-700 font-medium">{issue.expected_value}</span>
          </div>
        )}
        {issue.actual_value && (
          <div className="text-slate-600">
            <span className="font-medium text-slate-900">Extracted: </span>
            <span className="text-rose-700 font-medium">{issue.actual_value}</span>
          </div>
        )}
        <div className="text-slate-600">
          <span className="font-medium text-slate-900">Verification Confidence: </span>
          <span>{Math.round((issue.confidence_score || 0.9) * 100)}%</span>
        </div>
      </div>

      {/* Evidence snippet */}
      {issue.evidence_snippet && (
        <div className="mt-3 rounded-md bg-slate-100 p-2.5 text-xs text-slate-700 font-mono">
          <span className="font-sans font-semibold text-slate-500 block mb-0.5">Evidence Snippet:</span>
          "{issue.evidence_snippet}"
        </div>
      )}

      {/* RAG Grounded Explanation Box */}
      <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50/40 p-3.5 text-xs text-slate-800">
        <div className="flex items-center gap-1.5 font-semibold text-blue-900 mb-1">
          <ShieldCheck className="h-4 w-4 text-blue-600" />
          RAG-Grounded Explanation
        </div>
        <p className="leading-relaxed text-slate-700">{issue.explanation}</p>

        {/* Suggested Correction */}
        <div className="mt-2.5 flex items-start gap-1.5 rounded border border-emerald-200 bg-emerald-50/80 p-2 text-emerald-900 font-sans">
          <ArrowRight className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-emerald-800">Recommended Action: </span>
            <span>{issue.suggested_correction}</span>
          </div>
        </div>

        {/* Rule citation */}
        {issue.rag_source && (
          <div className="mt-2 flex items-center gap-1 text-[11px] text-blue-700 font-medium">
            <BookOpen className="h-3.5 w-3.5" />
            <span>Regulatory Basis: {issue.rag_source}</span>
            {issue.rag_rule_id && <span className="text-slate-400">({issue.rag_rule_id})</span>}
          </div>
        )}
      </div>
    </div>
  );
};
