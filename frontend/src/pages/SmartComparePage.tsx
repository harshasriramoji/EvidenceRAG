import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../api/client';
import {
  Columns2,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  ShieldAlert,
  Sparkles,
  Info
} from 'lucide-react';

export const SmartComparePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [documents, setDocuments] = useState<any[]>([]);
  const [docAId, setDocAId] = useState<number | null>(null);
  const [docBId, setDocBId] = useState<number | null>(null);
  const [docA, setDocA] = useState<any | null>(null);
  const [docB, setDocB] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await api.get('/documents');
        setDocuments(res.data);
        if (res.data.length >= 2) {
          setDocAId(res.data[0].id);
          setDocBId(res.data[1].id);
        } else if (res.data.length === 1) {
          setDocAId(res.data[0].id);
        }
      } catch (err) {
        console.error('Failed to load documents:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, []);

  useEffect(() => {
    const fetchDetails = async () => {
      if (!docAId || !docBId) return;
      setComparing(true);
      try {
        const [resA, resB] = await Promise.all([
          api.get(`/documents/${docAId}`),
          api.get(`/documents/${docBId}`)
        ]);
        setDocA(resA.data);
        setDocB(resB.data);
      } catch (err) {
        console.error('Error fetching document details for comparison:', err);
      } finally {
        setComparing(false);
      }
    };
    fetchDetails();
  }, [docAId, docBId]);

  // Build field comparison list
  const fieldsMap: Record<string, { valA?: string; valB?: string }> = {};

  if (docA && docA.extracted_fields) {
    docA.extracted_fields.forEach((f: any) => {
      if (!fieldsMap[f.field_name]) fieldsMap[f.field_name] = {};
      fieldsMap[f.field_name].valA = f.field_value;
    });
  }

  if (docB && docB.extracted_fields) {
    docB.extracted_fields.forEach((f: any) => {
      if (!fieldsMap[f.field_name]) fieldsMap[f.field_name] = {};
      fieldsMap[f.field_name].valB = f.field_value;
    });
  }

  const comparisonRows = Object.entries(fieldsMap).map(([fieldName, vals]) => {
    const a = (vals.valA || '').trim();
    const b = (vals.valB || '').trim();

    let status = 'Missing in one';
    let color = 'slate';
    let similarity = 0;

    if (a && b) {
      if (a.toLowerCase() === b.toLowerCase()) {
        status = 'Exact Match';
        color = 'emerald';
        similarity = 100;
      } else if (
        a.toLowerCase().replace(/[^a-z0-9]/g, '') === b.toLowerCase().replace(/[^a-z0-9]/g, '')
      ) {
        status = 'Soft Match (Formatting difference)';
        color = 'blue';
        similarity = 95;
      } else {
        status = 'Discrepancy Conflict';
        color = 'rose';
        similarity = 40;
      }
    }

    return {
      fieldName,
      valA: a || 'Not Extracted',
      valB: b || 'Not Extracted',
      status,
      color,
      similarity
    };
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Columns2 className="h-6 w-6 text-[#2563EB]" />
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Smart Document Comparison</h1>
        </div>
        <p className="mt-1 text-xs text-[#475569]">
          Side-by-side multi-credential field alignment with intelligent formatting tolerance and discrepancy detection.
        </p>
      </div>

      {/* Selectors Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 rounded-2xl border border-[#CBD5E1] bg-white p-4 shadow-sm">
        <div>
          <label className="block text-xs font-semibold text-[#0F172A] mb-1">Document A (Reference):</label>
          <select
            value={docAId || ''}
            onChange={(e) => setDocAId(Number(e.target.value))}
            className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.original_filename} ({d.category})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-[#0F172A] mb-1">Document B (Comparison Target):</label>
          <select
            value={docBId || ''}
            onChange={(e) => setDocBId(Number(e.target.value))}
            className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id} disabled={d.id === docAId}>
                {d.original_filename} ({d.category}) {d.id === docAId ? '(Already selected as Doc A)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Side-by-Side Document Panels */}
      {docA && docB && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Doc A Card */}
          <div className="rounded-2xl border border-blue-200 bg-white p-4 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-[#2563EB]">
                Document A
              </span>
              <span className="text-xs font-bold text-[#0F172A] truncate max-w-[200px]">
                {docA.original_filename}
              </span>
            </div>
            <div className="h-64 rounded-xl border border-slate-200 overflow-hidden bg-slate-50">
              <iframe
                src={`/api/documents/${docA.id}/preview`}
                title="Doc A Preview"
                className="w-full h-full"
              />
            </div>
            <div className="text-[11px] text-[#475569]">
              Category: <span className="font-semibold text-slate-800">{docA.category}</span> • Extracted Fields: {docA.extracted_fields?.length || 0}
            </div>
          </div>

          {/* Doc B Card */}
          <div className="rounded-2xl border border-purple-200 bg-white p-4 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="rounded bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-700">
                Document B
              </span>
              <span className="text-xs font-bold text-[#0F172A] truncate max-w-[200px]">
                {docB.original_filename}
              </span>
            </div>
            <div className="h-64 rounded-xl border border-slate-200 overflow-hidden bg-slate-50">
              <iframe
                src={`/api/documents/${docB.id}/preview`}
                title="Doc B Preview"
                className="w-full h-full"
              />
            </div>
            <div className="text-[11px] text-[#475569]">
              Category: <span className="font-semibold text-slate-800">{docB.category}</span> • Extracted Fields: {docB.extracted_fields?.length || 0}
            </div>
          </div>
        </div>
      )}

      {/* Field-by-Field Entity Comparison Matrix */}
      <div className="rounded-2xl border border-[#CBD5E1] bg-white p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-[#0F172A]">Field-Level Comparison Matrix</h3>
            <p className="text-xs text-[#475569]">
              Comparing canonical entities extracted from both uploaded credentials.
            </p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            {comparisonRows.length} Correlated Fields
          </span>
        </div>

        {comparisonRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#EFF6FF] text-[#1D4ED8] uppercase tracking-wider font-semibold border-b border-blue-200">
                <tr>
                  <th className="py-2.5 px-3">Field Entity</th>
                  <th className="py-2.5 px-3">Value in Document A</th>
                  <th className="py-2.5 px-3">Value in Document B</th>
                  <th className="py-2.5 px-3">Match Status</th>
                  <th className="py-2.5 px-3">Assessment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {comparisonRows.map((row) => (
                  <tr key={row.fieldName} className="hover:bg-slate-50">
                    <td className="py-3 px-3 font-semibold text-[#0F172A] capitalize">
                      {row.fieldName.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-800">
                      {row.valA}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-800">
                      {row.valB}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          row.color === 'emerald'
                            ? 'bg-emerald-100 text-emerald-800'
                            : row.color === 'blue'
                            ? 'bg-blue-100 text-blue-800'
                            : row.color === 'rose'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {row.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[11px] text-[#475569]">
                      {row.similarity === 100
                        ? 'Values match cleanly.'
                        : row.similarity >= 90
                        ? 'Benign punctuation / casing difference tolerated.'
                        : row.similarity > 0
                        ? 'Potential spelling / data conflict. Resolve before submit.'
                        : 'Information present only in one certificate.'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-[#475569]">
            Select two uploaded documents above to populate field comparison matrix.
          </div>
        )}
      </div>
    </div>
  );
};
