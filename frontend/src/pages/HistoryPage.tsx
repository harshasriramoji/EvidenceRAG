import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import {
  History,
  FileCheck2,
  Files,
  ArrowRight,
  Download,
  AlertTriangle,
  FileText
} from 'lucide-react';

export const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generatingId, setGeneratingId] = useState<number | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await api.get('/verify/history');
        setHistory(res.data);
      } catch (err) {
        console.error('Error fetching history:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const handleDownload = async (verificationId: number) => {
    setGeneratingId(verificationId);
    try {
      const res = await api.post(`/reports/generate/${verificationId}`);
      window.open(res.data.download_url, '_blank');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate report.');
    } finally {
      setGeneratingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Verification History</h1>
        <p className="mt-1 text-xs text-slate-500">
          Review previous single-document audits and multi-document cross-comparisons.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading audit history...</div>
        ) : history.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {history.map((item) => (
              <div key={item.id} className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-slate-900">Audit #{item.id}</span>
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700 capitalize">
                      {item.verification_mode === 'single' ? 'Mode A (Single)' : 'Mode B (Cross)'}
                    </span>
                    <StatusBadge status={item.overall_status} size="sm" />
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-1 max-w-xl">
                    {item.summary}
                  </p>
                  <div className="flex items-center gap-4 text-[11px] text-slate-400">
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                    <span>•</span>
                    <span className="text-rose-600 font-semibold">{item.critical_issues} Critical</span>
                    <span>•</span>
                    <span className="text-amber-600 font-semibold">{item.warning_issues} Warnings</span>
                    <span>•</span>
                    <span>{item.document_ids?.length || 1} Document(s)</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleDownload(item.id)}
                    disabled={generatingId === item.id}
                    className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                  >
                    <Download className="h-3.5 w-3.5" />
                    {generatingId === item.id ? 'Generating...' : 'PDF Report'}
                  </button>
                  <Link
                    to={item.verification_mode === 'single' ? `/verify/single?docId=${item.document_ids?.[0] || ''}` : '/verify/cross'}
                    className="flex items-center gap-1 rounded-lg bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700 hover:bg-brand-100"
                  >
                    View <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-slate-500">
            <History className="mx-auto h-8 w-8 text-slate-300 mb-2" />
            <p className="font-medium text-slate-700">No verification audits recorded yet.</p>
            <p className="mt-1">Run Mode A or Mode B to generate your first audit record.</p>
          </div>
        )}
      </div>
    </div>
  );
};
