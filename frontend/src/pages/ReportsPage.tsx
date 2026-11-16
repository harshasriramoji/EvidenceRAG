import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { FileText, Download, CheckCircle, Clock } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await api.get('/verify/history');
        setHistory(res.data);
      } catch (err) {
        console.error('Error fetching reports history:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const handleDownload = async (verificationId: number) => {
    setDownloadingId(verificationId);
    try {
      const res = await api.post(`/reports/generate/${verificationId}`);
      window.open(res.data.download_url, '_blank');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to download report.');
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Verification Reports</h1>
        <p className="mt-1 text-xs text-slate-500">
          Download branded, publication-grade PDF verification audit reports generated with ReportLab.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading reports...</div>
        ) : history.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {history.map((item) => (
              <div key={item.id} className="py-4 first:pt-0 last:pb-0 flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-brand-600 shrink-0">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-slate-900">
                      Audit Report — {item.verification_mode === 'single' ? 'Mode A (Single Document)' : 'Mode B (Multi-Document Cross-Verification)'}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Verification #{item.id} • Status: <span className="font-medium text-slate-700">{item.overall_status}</span> • {new Date(item.created_at).toLocaleDateString()}
                    </div>
                    <p className="text-[11px] text-slate-600 line-clamp-1 mt-1 max-w-md">
                      {item.summary}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => handleDownload(item.id)}
                  disabled={downloadingId === item.id}
                  className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-slate-800 disabled:opacity-50 transition-colors"
                >
                  <Download className="h-4 w-4" />
                  {downloadingId === item.id ? 'Generating...' : 'Download PDF'}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-slate-500">
            <FileText className="mx-auto h-8 w-8 text-slate-300 mb-2" />
            <p className="font-medium text-slate-700">No reports generated yet.</p>
            <p className="mt-1">Execute a verification audit first to download its PDF report.</p>
          </div>
        )}
      </div>
    </div>
  );
};
