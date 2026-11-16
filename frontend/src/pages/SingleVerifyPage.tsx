import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { RAGExplanationCard, IssueItem } from '../components/RAGExplanationCard';
import {
  FileCheck2,
  FileText,
  AlertOctagon,
  Download,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  Filter,
  Eye,
  Info
} from 'lucide-react';

export const SingleVerifyPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(
    searchParams.get('docId') ? parseInt(searchParams.get('docId')!) : null
  );
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await api.get('/documents');
        setDocuments(res.data);
        if (!selectedDocId && res.data.length > 0) {
          setSelectedDocId(res.data[0].id);
        }
      } catch (err) {
        console.error('Error fetching documents:', err);
      } finally {
        setLoadingDocs(false);
      }
    };
    fetchDocs();
  }, []);

  const handleVerify = async () => {
    if (!selectedDocId) {
      setError('Please select a document to verify.');
      return;
    }
    setVerifying(true);
    setError(null);
    try {
      const res = await api.post(`/verify/document/${selectedDocId}`);
      setVerificationResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Single document verification failed.');
    } finally {
      setVerifying(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!verificationResult) return;
    setGeneratingReport(true);
    try {
      const res = await api.post(`/reports/generate/${verificationResult.id}`);
      window.open(res.data.download_url, '_blank');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate PDF report.');
    } finally {
      setGeneratingReport(false);
    }
  };

  const filteredIssues = verificationResult?.issues?.filter((iss: IssueItem) => {
    if (selectedSeverity === 'all') return true;
    if (selectedSeverity === 'review') return iss.manual_review_recommended;
    return iss.severity.toLowerCase() === selectedSeverity.toLowerCase();
  }) || [];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 uppercase tracking-wider">
              Mode A
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Single Document Verification</h1>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Verify an individual credential independently for compliance, missing fields, invalid dates, and quality flaws.
          </p>
        </div>

        {verificationResult && (
          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-slate-800 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {generatingReport ? 'Generating PDF...' : 'Download Audit Report PDF'}
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Document Selector Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <label className="block text-xs font-semibold text-slate-800">
          Choose Uploaded Document to Audit:
        </label>

        {loadingDocs ? (
          <div className="text-xs text-slate-400">Loading documents...</div>
        ) : documents.length > 0 ? (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => setSelectedDocId(doc.id)}
                className={`flex items-center gap-3 rounded-xl border p-3 cursor-pointer transition-all ${
                  selectedDocId === doc.id
                    ? 'border-emerald-500 bg-emerald-50/40 ring-1 ring-emerald-500'
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <FileText className={`h-6 w-6 shrink-0 ${selectedDocId === doc.id ? 'text-emerald-600' : 'text-slate-400'}`} />
                <div className="truncate">
                  <div className="text-xs font-semibold text-slate-900 truncate">{doc.original_filename}</div>
                  <div className="text-[11px] text-slate-500">{doc.category}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-slate-500">
            No documents uploaded.{' '}
            <Link to="/upload" className="font-semibold text-brand-600 underline">
              Upload a document now
            </Link>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            onClick={handleVerify}
            disabled={verifying || !selectedDocId}
            className="flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            {verifying ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Auditing & Retrieving RAG Rules...
              </>
            ) : (
              <>
                <FileCheck2 className="h-4 w-4" />
                Run Single-Document Verification (Mode A)
              </>
            )}
          </button>
        </div>
      </div>

      {/* Verification Results View */}
      {verificationResult && (
        <div className="space-y-6">
          {/* Outcome Header Banner */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Verification Result</span>
                <div className="mt-1 flex items-center gap-3">
                  <StatusBadge status={verificationResult.overall_status} size="lg" />
                  <span className="text-xs text-slate-500">
                    Audit #{verificationResult.id} • {new Date(verificationResult.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs">
                <div className="text-center">
                  <div className="text-lg font-bold text-rose-600">{verificationResult.critical_issues}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-medium">Critical Issues</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-amber-600">{verificationResult.warning_issues}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-medium">Warnings</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-slate-700">{verificationResult.total_issues}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-medium">Total Defects</div>
                </div>
              </div>
            </div>

            <p className="mt-4 text-xs text-slate-700 leading-relaxed font-sans">
              <span className="font-semibold text-slate-900">Audit Summary: </span>
              {verificationResult.summary}
            </p>
          </div>

          {/* Issue Filters */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
              <Filter className="h-4 w-4 text-slate-400" />
              Filter Detected Issues:
            </div>
            <div className="flex flex-wrap gap-1.5">
              {[
                { id: 'all', label: `All (${verificationResult.issues?.length || 0})` },
                { id: 'critical', label: `Critical (${verificationResult.critical_issues})` },
                { id: 'high', label: 'High' },
                { id: 'medium', label: 'Medium' },
                { id: 'review', label: 'Manual Review' }
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setSelectedSeverity(f.id)}
                  className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
                    selectedSeverity === f.id
                      ? 'bg-slate-900 text-white font-semibold'
                      : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Issues List with Grounded RAG explanations */}
          {filteredIssues.length > 0 ? (
            <div className="space-y-4">
              {filteredIssues.map((issue: IssueItem, idx: number) => (
                <RAGExplanationCard key={idx} issue={issue} index={idx + 1} />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-8 text-center text-xs text-emerald-800">
              <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600 mb-2" />
              <div className="font-semibold text-sm">No issues under this filter.</div>
              <p className="mt-1">The evaluated criteria fulfilled compliance guidelines.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
