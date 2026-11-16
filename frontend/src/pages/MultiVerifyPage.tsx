import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { RAGExplanationCard, IssueItem } from '../components/RAGExplanationCard';
import {
  Files,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Filter,
  Layers,
  ArrowRight
} from 'lucide-react';

export const MultiVerifyPage: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'matrix' | 'issues'>('matrix');

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await api.get('/documents');
        setDocuments(res.data);
        // Pre-select first 4 if available
        if (res.data.length >= 2) {
          setSelectedIds(res.data.slice(0, Math.min(res.data.length, 4)).map((d: any) => d.id));
        }
      } catch (err) {
        console.error('Error loading documents:', err);
      } finally {
        setLoadingDocs(false);
      }
    };
    fetchDocs();
  }, []);

  const toggleSelectDoc = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === documents.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(documents.map((d) => d.id));
    }
  };

  const handleCrossVerify = async () => {
    if (selectedIds.length < 2) {
      setError('Please select at least 2 documents for cross-verification.');
      return;
    }
    setVerifying(true);
    setError(null);
    try {
      const res = await api.post('/verify/multiple', { document_ids: selectedIds });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Multi-document verification failed.');
    } finally {
      setVerifying(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!result) return;
    setGeneratingReport(true);
    try {
      const res = await api.post(`/reports/generate/${result.id}`);
      window.open(res.data.download_url, '_blank');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate PDF report.');
    } finally {
      setGeneratingReport(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-brand-100 px-2 py-0.5 text-[10px] font-bold text-brand-800 uppercase tracking-wider">
              Mode B
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Multi-Document Cross-Verification</h1>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Compare demographic and financial values across multiple credentials to spot mismatches before final submission.
          </p>
        </div>

        {result && (
          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-slate-800 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {generatingReport ? 'Generating Combined Report...' : 'Download Combined Audit Report PDF'}
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Multi-Document Selector Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-slate-800">
            Select 2 or More Documents to Compare ({selectedIds.length} selected):
          </label>
          {documents.length > 0 && (
            <button
              onClick={selectAll}
              className="text-xs font-medium text-brand-600 hover:underline"
            >
              {selectedIds.length === documents.length ? 'Deselect All' : 'Select All'}
            </button>
          )}
        </div>

        {loadingDocs ? (
          <div className="text-xs text-slate-400">Loading documents...</div>
        ) : documents.length > 0 ? (
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {documents.map((doc) => {
              const isSelected = selectedIds.includes(doc.id);
              return (
                <div
                  key={doc.id}
                  onClick={() => toggleSelectDoc(doc.id)}
                  className={`flex items-start gap-2.5 rounded-xl border p-3 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-brand-500 bg-brand-50/50 ring-1 ring-brand-500'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}} // handled by parent onClick
                    className="mt-0.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
                  <div className="truncate">
                    <div className="text-xs font-semibold text-slate-900 truncate">{doc.original_filename}</div>
                    <div className="text-[11px] text-slate-500">{doc.category}</div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-xs text-slate-500">
            No documents uploaded.{' '}
            <Link to="/upload" className="font-semibold text-brand-600 underline">
              Upload documents
            </Link>{' '}
            or import from{' '}
            <Link to="/dataset" className="font-semibold text-purple-700 underline">
              Dataset Applicant Folders
            </Link>.
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            onClick={handleCrossVerify}
            disabled={verifying || selectedIds.length < 2}
            className="flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {verifying ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Cross-Comparing Fields & Synthesizing Explanations...
              </>
            ) : (
              <>
                <Files className="h-4 w-4" />
                Run Cross-Verification (Mode B)
              </>
            )}
          </button>
        </div>
      </div>

      {/* Cross-Verification Results */}
      {result && (
        <div className="space-y-6">
          {/* Status Overview Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Cross-Verification Result</span>
                <div className="mt-1 flex items-center gap-3">
                  <StatusBadge status={result.overall_status} size="lg" />
                  <span className="text-xs text-slate-500">
                    Audit #{result.id} • {new Date(result.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs">
                <div className="text-center">
                  <div className="text-lg font-bold text-rose-600">{result.critical_issues}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-medium">Critical Mismatches</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-amber-600">{result.warning_issues}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-medium">Warnings</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-brand-700">{result.cross_comparisons?.length || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-medium">Shared Fields Checked</div>
                </div>
              </div>
            </div>

            <p className="mt-4 text-xs text-slate-700 leading-relaxed">
              <span className="font-semibold text-slate-900">Summary: </span>
              {result.summary}
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-200">
            <button
              onClick={() => setActiveTab('matrix')}
              className={`flex items-center gap-2 border-b-2 py-2 px-4 text-xs font-semibold ${
                activeTab === 'matrix'
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Layers className="h-4 w-4" />
              Field Comparison Matrix ({result.cross_comparisons?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('issues')}
              className={`flex items-center gap-2 border-b-2 py-2 px-4 text-xs font-semibold ${
                activeTab === 'issues'
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <AlertTriangle className="h-4 w-4" />
              Detected Issues & RAG Explanations ({result.issues?.length || 0})
            </button>
          </div>

          {/* Tab 1: Comparison Matrix */}
          {activeTab === 'matrix' && (
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
              {result.cross_comparisons && result.cross_comparisons.length > 0 ? (
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Field Name</th>
                      <th className="py-2.5 px-3">Document A & Value</th>
                      <th className="py-2.5 px-3">Document B & Value</th>
                      <th className="py-2.5 px-3">Status / Similarity</th>
                      <th className="py-2.5 px-3">Recommendation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.cross_comparisons.map((cmp: any, idx: number) => (
                      <tr key={idx} className={cmp.is_match ? 'hover:bg-slate-50' : 'bg-rose-50/20 hover:bg-rose-50/30'}>
                        <td className="py-3 px-3 font-semibold text-slate-900">{cmp.field_name}</td>
                        <td className="py-3 px-3 text-slate-700">
                          <div className="font-medium text-slate-900 truncate max-w-[160px]">{cmp.doc_a_name}</div>
                          <div className="text-[11px] text-slate-500 font-mono mt-0.5">{cmp.val_a || 'null'}</div>
                        </td>
                        <td className="py-3 px-3 text-slate-700">
                          <div className="font-medium text-slate-900 truncate max-w-[160px]">{cmp.doc_b_name}</div>
                          <div className="text-[11px] text-slate-500 font-mono mt-0.5">{cmp.val_b || 'null'}</div>
                        </td>
                        <td className="py-3 px-3">
                          {cmp.is_match ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              Match ({Math.round(cmp.similarity_score * 100)}%)
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700 border border-rose-200">
                              <XCircle className="h-3.5 w-3.5" />
                              Mismatch ({Math.round(cmp.similarity_score * 100)}%)
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-slate-600 text-[11px]">
                          {cmp.recommendation}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500">
                  No shared fields directly overlapped between the selected document types.
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Issues and RAG explanations */}
          {activeTab === 'issues' && (
            <div className="space-y-4">
              {result.issues && result.issues.length > 0 ? (
                result.issues.map((issue: IssueItem, idx: number) => (
                  <RAGExplanationCard key={idx} issue={issue} index={idx + 1} />
                ))
              ) : (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-8 text-center text-xs text-emerald-800">
                  <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600 mb-2" />
                  <div className="font-semibold text-sm">Clean Cross-Verification!</div>
                  <p className="mt-1">All shared credentials aligned with high statistical similarity.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
