import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  ArrowRight,
  ShieldCheck,
  FileCheck2,
  Files
} from 'lucide-react';

const CATEGORIES = [
  "Aadhaar Card",
  "Income Certificate",
  "Caste Certificate",
  "Residence Certificate",
  "Study Certificate",
  "Bonafide Certificate",
  "Marks Memo",
  "Bank Passbook",
  "Passport-size Photograph",
  "Other Supporting Documents"
];

export const DocumentUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedCategory, setSelectedCategory] = useState<string>("Aadhaar Card");
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedResults, setUploadedResults] = useState<any[] | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...newFiles]);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      setFiles((prev) => [...prev, ...droppedFiles]);
      setError(null);
    }
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError("Please select at least one document to upload.");
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("category", selectedCategory);
    files.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const res = await api.post("/documents/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setUploadedResults(res.data);
      setFiles([]);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload or OCR processing failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Upload Scholarship Documents</h1>
        <p className="mt-1 text-xs text-slate-500">
          Upload PDF or image files (JPG, PNG) for multi-engine OCR extraction, quality audit, and verification.
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Upload Validation Error: </span>
            {error}
          </div>
        </div>
      )}

      {/* Upload Success View */}
      {uploadedResults && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-6 space-y-4">
          <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <span>Successfully Processed {uploadedResults.length} Document(s)</span>
          </div>
          <p className="text-xs text-slate-600">
            Multi-engine OCR extracted text and detected structural attributes. Choose your next step:
          </p>

          <div className="divide-y divide-emerald-100 rounded-xl border border-emerald-200 bg-white p-4">
            {uploadedResults.map((doc) => (
              <div key={doc.id} className="py-2.5 first:pt-0 last:pb-0 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-slate-900">{doc.original_filename}</div>
                  <div className="text-[11px] text-slate-500">
                    Category: <span className="font-medium text-slate-700">{doc.category}</span> • Extracted Fields: {doc.extracted_fields?.length || 0}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Link
                    to={`/verify/single?docId=${doc.id}`}
                    className="flex items-center gap-1 rounded bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-700"
                  >
                    <FileCheck2 className="h-3.5 w-3.5" /> Verify (Mode A)
                  </Link>
                  <Link
                    to={`/documents/${doc.id}`}
                    className="rounded border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    View Details
                  </Link>
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              to="/verify/cross"
              className="flex items-center gap-1.5 rounded-lg bg-[#2563EB] px-4 py-2 text-xs font-semibold text-white shadow hover:bg-[#1D4ED8]"
            >
              <Files className="h-4 w-4" />
              Go to Multi-Document Cross-Verification (Mode B)
            </Link>
            <button
              onClick={() => setUploadedResults(null)}
              className="rounded-lg border border-[#CBD5E1] bg-white px-4 py-2 text-xs font-medium text-[#0F172A] hover:bg-slate-50 cursor-pointer"
            >
              Upload More Documents
            </button>
          </div>
        </div>
      )}

      {/* Main Upload Card */}
      {!uploadedResults && (
        <div className="rounded-2xl border border-[#CBD5E1] bg-white p-6 shadow-sm space-y-6">
          {/* Category Selector */}
          <div>
            <label className="block text-xs font-semibold text-[#0F172A] mb-2">
              Select Document Category
            </label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`rounded-lg border p-2.5 text-left text-xs font-medium transition-all cursor-pointer ${
                    selectedCategory === cat
                      ? 'border-[#2563EB] bg-blue-50 text-[#2563EB] font-semibold ring-1 ring-[#2563EB]'
                      : 'border-[#CBD5E1] bg-white text-[#475569] hover:border-slate-400 hover:bg-slate-50'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Drag & Drop Area */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#CBD5E1] bg-[#F8FAFF] p-8 text-center hover:border-[#2563EB] hover:bg-blue-50/20 transition-all cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              multiple
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
            />
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-100 text-[#2563EB] mb-3">
              <UploadCloud className="h-6 w-6" />
            </div>
            <p className="text-sm font-semibold text-[#0F172A]">
              Drag and drop files here, or <span className="text-[#2563EB] underline">browse</span>
            </p>
            <p className="mt-1 text-xs text-[#475569]">
              Supported formats: PDF, JPG, JPEG, PNG (Max size: 25MB per file)
            </p>
          </div>

          {/* Staged Files Queue */}
          {files.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-[#0F172A] mb-2">
                Staged for Ingestion ({files.length} file{files.length > 1 ? 's' : ''}):
              </div>
              <div className="space-y-2">
                {files.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-lg border border-[#CBD5E1] bg-[#F8FAFF] px-3 py-2 text-xs"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <FileText className="h-4 w-4 text-[#2563EB] shrink-0" />
                      <span className="font-medium text-[#0F172A] truncate">{file.name}</span>
                      <span className="text-[#475569] text-[11px]">
                        ({(file.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      className="text-slate-400 hover:text-rose-600 cursor-pointer"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex justify-end">
                <button
                  type="button"
                  disabled={uploading}
                  onClick={handleUpload}
                  className="flex items-center gap-2 rounded-xl bg-[#2563EB] px-6 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-[#1D4ED8] disabled:opacity-50 transition-colors cursor-pointer"
                >
                  {uploading ? (
                    <>
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Processing OCR & Extracting...
                    </>
                  ) : (
                    <>
                      Upload and Extract ({files.length})
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
