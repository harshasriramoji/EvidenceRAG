import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import {
  FileText,
  FileCheck2,
  Trash2,
  Download,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Eye,
  Copy,
  Check
} from 'lucide-react';

export const DocumentDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [document, setDocument] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        const res = await api.get(`/documents/${id}`);
        setDocument(res.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load document details.');
      } finally {
        setLoading(false);
      }
    };
    fetchDoc();
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this document from your repository?')) return;
    try {
      await api.delete(`/documents/${id}`);
      navigate('/dashboard');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete document.');
    }
  };

  const copyText = () => {
    if (document?.raw_text) {
      navigator.clipboard.writeText(document.raw_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-400">Loading document details...</div>;
  }

  if (error || !document) {
    return (
      <div className="p-8 text-center text-xs text-rose-600">
        <p>{error || 'Document not found.'}</p>
        <Link to="/dashboard" className="mt-3 inline-block font-semibold text-brand-600 underline">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link to="/dashboard" className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 mb-2">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">{document.original_filename}</h1>
            <span className="rounded bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700 border border-brand-200">
              {document.category}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Uploaded on {new Date(document.created_at).toLocaleString()} • {(document.file_size / 1024).toFixed(1)} KB • {document.mime_type}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to={`/verify/single?docId=${document.id}`}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-emerald-700"
          >
            <FileCheck2 className="h-4 w-4" />
            Verify (Mode A)
          </Link>
          <a
            href={`/api/documents/${document.id}/preview`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            <Download className="h-4 w-4" />
            Raw File
          </a>
          <button
            onClick={handleDelete}
            className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-rose-700 hover:bg-rose-100"
            title="Delete Document"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Quality Indicators Card */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm text-xs">
          <span className="text-slate-500 block">Quality Score</span>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {Math.round((document.quality_score || 0.8) * 100)}%
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm text-xs">
          <span className="text-slate-500 block">Blur Analysis</span>
          <div className="mt-1 font-semibold">
            {document.is_blurry ? (
              <span className="text-rose-600">Blurry Scan</span>
            ) : (
              <span className="text-emerald-600">Sharp Contrast</span>
            )}
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm text-xs">
          <span className="text-slate-500 block">Resolution Health</span>
          <div className="mt-1 font-semibold">
            {document.is_low_res ? (
              <span className="text-amber-600">Low Resolution</span>
            ) : (
              <span className="text-emerald-600">Optimal (150+ DPI)</span>
            )}
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm text-xs">
          <span className="text-slate-500 block">Page Count</span>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {document.page_count || 1} Page(s)
          </div>
        </div>
      </div>

      {/* Extracted Fields Table */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-1">OCR Extracted Information Fields</h3>
        <p className="text-xs text-slate-500 mb-4">
          Structured entities identified via regular expression and layout parsing
        </p>

        {document.extracted_fields && document.extracted_fields.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Field Name</th>
                  <th className="py-2.5 px-3">Extracted Value</th>
                  <th className="py-2.5 px-3">Extraction Confidence</th>
                  <th className="py-2.5 px-3">Page</th>
                  <th className="py-2.5 px-3">Method</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {document.extracted_fields.map((field: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-semibold text-slate-900 capitalize">
                      {field.field_name.replace('_', ' ')}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-800">
                      {field.field_value || <span className="text-slate-400">null</span>}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="rounded bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-700">
                        {Math.round((field.confidence || 0.9) * 100)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">{field.page_number}</td>
                    <td className="py-2.5 px-3 text-slate-500 text-[11px] uppercase">{field.extraction_method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-xs text-slate-400 py-4 text-center">
            No specific structured fields could be parsed from this document.
          </div>
        )}
      </div>

      {/* Raw Extracted Text Viewer */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Raw OCR Extracted Text</h3>
            <p className="text-xs text-slate-500">Unprocessed text extracted directly from document scan</p>
          </div>
          <button
            onClick={copyText}
            className="flex items-center gap-1 rounded border border-slate-200 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy Text'}
          </button>
        </div>
        <div className="rounded-xl bg-slate-900 p-4 font-mono text-xs text-slate-100 leading-relaxed max-h-72 overflow-y-auto whitespace-pre-wrap">
          {document.raw_text || '[No text detected by OCR engine]'}
        </div>
      </div>
    </div>
  );
};
