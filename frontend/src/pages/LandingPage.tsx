import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  FileCheck2,
  Files,
  Cpu,
  FileSearch,
  CheckCircle,
  Database,
  ArrowRight,
  DownloadCloud,
  Layers,
  Sparkles
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F8FAFF] text-[#0F172A]">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-[#CBD5E1] bg-white py-20 lg:py-28">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50/70 via-transparent to-transparent pointer-events-none" />
        
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative">
          <div className="mx-auto max-w-3xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3.5 py-1 text-xs font-semibold text-[#2563EB] mb-6 shadow-xs">
              <Sparkles className="h-3.5 w-3.5 text-[#2563EB]" />
              Explainable Pre-Submission Application Verification
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight text-[#0F172A] sm:text-5xl lg:text-6xl">
              Verify Scholarship Applications with <span className="bg-gradient-to-r from-[#2563EB] to-[#7C3AED] bg-clip-text text-transparent">EvidenceRAG</span>
            </h1>

            <p className="mt-6 text-base text-[#475569] sm:text-lg leading-relaxed">
              Detect mistakes in individual documents, cross-compare certificates for conflicting information, 
              and receive regulatory-grounded explanations powered by Retrieval-Augmented Generation before submitting.
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/register"
                className="flex items-center gap-2 rounded-xl bg-[#2563EB] px-6 py-3 text-sm font-semibold text-white shadow-md hover:bg-[#1D4ED8] transition-all hover:shadow-lg"
              >
                Start Verification
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/login"
                className="flex items-center gap-2 rounded-xl border border-[#CBD5E1] bg-white px-6 py-3 text-sm font-semibold text-[#0F172A] hover:bg-slate-50 transition-all"
              >
                Sign In to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Two Core Verification Modes */}
      <section className="py-16 bg-[#F8FAFF] border-b border-[#CBD5E1]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Two Mandatory Verification Engines
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Designed for end-to-end reliability, rigorous compliance checking, and cross-credential integrity.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            {/* Mode A: Single Document */}
            <div className="rounded-2xl border border-emerald-100 bg-white p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 font-bold">
                  <FileCheck2 className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">Mode A</span>
                  <h3 className="text-xl font-bold text-slate-900">Single Document Verification</h3>
                </div>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed mb-6">
                Upload only one certificate and independently audit it for 20+ defects without requiring any supporting documents.
              </p>
              <ul className="space-y-2.5 text-xs text-slate-700">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Missing mandatory fields (Name, UID, Income, DOB, Issue Date)</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Invalid and impossible dates (e.g. 31/02/2024, future dates)</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Expired certificates based on configured rules (e.g. 12-month income validity)</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Image quality analysis (Laplacian blur, low-res, rotated documents)</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Signature and departmental seal indicator checks with manual review recommendation</span>
                </li>
              </ul>
            </div>

            {/* Mode B: Multi Document Cross-Verification */}
            <div className="rounded-2xl border border-brand-100 bg-white p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-100 text-brand-700 font-bold">
                  <Files className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-brand-700">Mode B</span>
                  <h3 className="text-xl font-bold text-slate-900">Multi-Document Cross-Verification</h3>
                </div>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed mb-6">
                Upload multiple documents (Aadhaar, Income, Caste, Passbook, Bonafide) and automatically cross-compare shared fields.
              </p>
              <ul className="space-y-2.5 text-xs text-slate-700">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-brand-600 shrink-0" />
                  <span>Full name alignment across all submitted credentials</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-brand-600 shrink-0" />
                  <span>Date of birth (DOB) consistency verification</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-brand-600 shrink-0" />
                  <span>Address & domicile alignment across state documents</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-brand-600 shrink-0" />
                  <span>Handles harmless differences (spaces, casing, abbreviations, honorifics)</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-brand-600 shrink-0" />
                  <span>Combined multi-document verification audit report generation</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* RAG Explainability Pipeline */}
      <section className="py-16 bg-white border-b border-slate-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Retrieval-Augmented Generation (RAG) Architecture
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Every flagged issue is grounded in regulatory verification rules, offering clear explanations and recommended actions.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-bold mb-3">
                1
              </div>
              <h4 className="font-semibold text-slate-900 mb-1">OCR & Ingestion</h4>
              <p className="text-xs text-slate-600">
                PyMuPDF + OpenCV + Tesseract OCR process PDFs and images, evaluating blur and extracting text.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-bold mb-3">
                2
              </div>
              <h4 className="font-semibold text-slate-900 mb-1">Issue Detection</h4>
              <p className="text-xs text-slate-600">
                Rule engine and field comparators discover missing fields, invalid dates, and cross-document mismatches.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-bold mb-3">
                3
              </div>
              <h4 className="font-semibold text-slate-900 mb-1">Vector Knowledge Lookup</h4>
              <p className="text-xs text-slate-600">
                TF-IDF & semantic vector search retrieves official scholarship guidelines for each detected defect.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-bold mb-3">
                4
              </div>
              <h4 className="font-semibold text-slate-900 mb-1">Grounded Explanation</h4>
              <p className="text-xs text-slate-600">
                Ollama LLM or deterministic fallback synthesizes plain-English explanations with citations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="py-16 bg-gradient-to-r from-[#1D4ED8] to-[#2563EB] text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl text-white">
            Pre-Submission Verification With Real User Documents
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-sm text-blue-100 leading-relaxed">
            Upload your actual scholarship documents (Aadhaar Card, Income Certificate, Caste Certificate, Bonafide, Bank Passbook, Marks Memos) 
            to identify non-compliance before submission. Every finding is referenced against statutory government portal norms.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/register"
              className="flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-[#1D4ED8] shadow-md hover:bg-blue-50 transition-all"
            >
              <ShieldCheck className="h-4 w-4" />
              Create Free Student Account
            </Link>
            <Link
              to="/login"
              className="flex items-center gap-2 rounded-xl border border-blue-300/40 bg-blue-700/50 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-800/50 transition-all"
            >
              Sign In to Your Workspace
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-500">
        <div className="mx-auto max-w-7xl px-4">
          <p>© 2026 EvidenceRAG — Explainable Pre-Submission Application Verification Using Retrieval-Augmented Generation.</p>
          <p className="mt-1">Built with React, Vite, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy, Scikit-learn, ReportLab, and Ollama.</p>
        </div>
      </footer>
    </div>
  );
};
