import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import {
  History,
  ArrowLeft,
  Upload,
  CheckCircle2,
  Clock,
  FileText,
  AlertCircle,
  Plus,
  RefreshCw,
  Eye,
  ShieldCheck
} from 'lucide-react';

interface VersionItem {
  id: number;
  version_number: number;
  file_size: number;
  quality_score: number;
  change_summary: string;
  created_at: string;
  is_current?: boolean;
}

interface VersionData {
  document_id: number;
  document_name: string;
  category: string;
  current_version: number;
  total_versions: number;
  versions: VersionItem[];
}

export const VersionHistoryPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<VersionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Version Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [changeSummary, setChangeSummary] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const fetchVersions = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/documents/${id}/versions`);
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load document version history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchVersions();
    }
  }, [id]);

  const handleUploadNewVersion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !id) return;

    setUploading(true);
    setUploadSuccess(null);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('change_summary', changeSummary || 'Uploaded corrected scan');

    try {
      const res = await api.post(`/documents/${id}/versions`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadSuccess(res.data.message || 'New version processed successfully.');
      setSelectedFile(null);
      setChangeSummary('');
      fetchVersions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload new document version.');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center text-xs text-[#475569]">
        <RefreshCw className="h-6 w-6 animate-spin text-[#2563EB] mr-2" />
        Retrieving document version records and historical revisions...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to={id ? `/documents/${id}` : '/dashboard'}
            className="flex items-center gap-1 rounded-lg border border-[#CBD5E1] bg-white px-3 py-1.5 text-xs font-semibold text-[#0F172A] hover:bg-slate-50 cursor-pointer transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Document
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-[#2563EB] uppercase tracking-wider">
                Version History
              </span>
              <span className="text-xs text-[#475569]">
                {data?.category} • ID #{data?.document_id}
              </span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-[#0F172A] mt-0.5">
              {data?.document_name}
            </h1>
          </div>
        </div>

        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800 self-start sm:self-center">
          Active: Version {data?.current_version}
        </span>
      </div>

      {uploadSuccess && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 text-xs font-semibold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          {uploadSuccess}
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-semibold text-rose-800 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-rose-600" />
          {error}
        </div>
      )}

      {/* Upload New Version Card */}
      <div className="rounded-2xl border border-blue-200 bg-gradient-to-r from-blue-50/50 via-white to-purple-50/30 p-5 shadow-xs space-y-3">
        <div className="flex items-center gap-2 text-sm font-bold text-[#0F172A]">
          <Upload className="h-4 w-4 text-[#2563EB]" />
          <span>Upload Corrected Version (Re-scan / Resolution)</span>
        </div>
        <p className="text-xs text-[#475569]">
          Uploading a corrected certificate scan preserves previous audit results while re-running OCR extraction on the new version.
        </p>

        <form onSubmit={handleUploadNewVersion} className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-2">
          <div className="md:col-span-5">
            <input
              type="file"
              required
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full rounded-lg border border-[#CBD5E1] bg-white p-1.5 text-xs text-[#0F172A] file:mr-2 file:rounded file:border-0 file:bg-blue-50 file:px-2.5 file:py-1 file:text-xs file:font-semibold file:text-[#2563EB]"
            />
          </div>

          <div className="md:col-span-5">
            <input
              type="text"
              value={changeSummary}
              onChange={(e) => setChangeSummary(e.target.value)}
              placeholder="Revision notes (e.g., 'Rescanned at 300 DPI with visible stamp')"
              className="w-full rounded-lg border border-[#CBD5E1] bg-white px-3 py-2 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none"
            />
          </div>

          <div className="md:col-span-2">
            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="w-full flex items-center justify-center gap-1.5 rounded-lg bg-[#2563EB] px-3 py-2 text-xs font-semibold text-white shadow hover:bg-[#1D4ED8] disabled:opacity-50 cursor-pointer transition-colors"
            >
              {uploading ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <>
                  <Plus className="h-3.5 w-3.5" /> Submit v{(data?.current_version || 1) + 1}
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Version Timeline Card */}
      <div className="rounded-2xl border border-[#CBD5E1] bg-white p-6 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-[#0F172A]">Revision Timeline</h3>

        <div className="relative border-l-2 border-blue-200 ml-4 space-y-6 py-2">
          {data?.versions.map((ver, idx) => (
            <div key={idx} className="relative pl-6">
              {/* Timeline marker */}
              <div
                className={`absolute -left-2 top-1 h-3.5 w-3.5 rounded-full border-2 bg-white ${
                  ver.is_current ? 'border-emerald-600 ring-4 ring-emerald-100' : 'border-[#2563EB]'
                }`}
              />

              <div className="rounded-xl border border-slate-200 bg-[#F8FAFF] p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-bold ${
                        ver.is_current
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-slate-200 text-slate-800'
                      }`}
                    >
                      Version {ver.version_number} {ver.is_current ? '(Current Active)' : '(Archived)'}
                    </span>
                    <span className="text-[11px] text-[#475569]">
                      {new Date(ver.created_at).toLocaleString()}
                    </span>
                  </div>

                  <span className="text-[11px] font-mono text-[#475569]">
                    Size: {(ver.file_size / 1024).toFixed(1)} KB
                  </span>
                </div>

                <p className="text-xs text-[#0F172A] font-medium leading-relaxed">
                  {ver.change_summary}
                </p>

                <div className="flex items-center justify-between pt-1 border-t border-slate-200 text-[11px] text-[#475569]">
                  <span>Visual Focus Quality Score: {(ver.quality_score * 100).toFixed(0)}%</span>
                  {ver.is_current && id && (
                    <Link
                      to={`/verify/single?docId=${id}`}
                      className="text-[#2563EB] hover:underline font-semibold"
                    >
                      Run Mode A Verification →
                    </Link>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
