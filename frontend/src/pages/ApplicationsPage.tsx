import React, { useState, useEffect } from 'react';
import { Plus, FolderCheck, Send, Paperclip, Clock, AlertCircle, CheckCircle2, ChevronRight, FileText } from 'lucide-react';
import api from '../api/client';

interface ApplicationItem {
  id: number;
  application_number: string;
  title: string;
  scholarship_name: string;
  status: string;
  academic_year: string;
  notes?: string;
  reviewer_notes?: string;
  submitted_at?: string;
  created_at: string;
  documents: Array<{
    id: number;
    filename: string;
    original_filename: string;
    category: string;
    upload_status: string;
  }>;
}

interface UserDoc {
  id: number;
  original_filename: string;
  category: string;
}

export const ApplicationsPage: React.FC = () => {
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [userDocs, setUserDocs] = useState<UserDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAttachModal, setShowAttachModal] = useState<number | null>(null);

  // Form states
  const [newTitle, setNewTitle] = useState('');
  const [newScheme, setNewScheme] = useState('National Scholarship Scheme');
  const [newAcademicYear, setNewAcademicYear] = useState('2025-2026');
  const [newNotes, setNewNotes] = useState('');
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const [appRes, docsRes] = await Promise.all([
        api.get('/applications'),
        api.get('/documents')
      ]);
      setApplications(appRes.data);
      setUserDocs(docsRes.data);
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: 'Failed to load applications.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/applications', {
        title: newTitle,
        scholarship_name: newScheme,
        academic_year: newAcademicYear,
        notes: newNotes
      });
      setMessage({ type: 'success', text: 'Application created successfully!' });
      setShowCreateModal(false);
      setNewTitle('');
      setNewNotes('');
      fetchApplications();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to create application.' });
    }
  };

  const handleAttach = async (appId: number) => {
    if (!selectedDocId) return;
    try {
      await api.post(`/applications/${appId}/attach-document/${selectedDocId}`);
      setMessage({ type: 'success', text: 'Document attached to application!' });
      setShowAttachModal(null);
      setSelectedDocId(null);
      fetchApplications();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to attach document.' });
    }
  };

  const handleSubmit = async (appId: number) => {
    if (!confirm('Are you sure you want to submit this application for official evaluation?')) return;
    try {
      await api.post(`/applications/${appId}/submit`);
      setMessage({ type: 'success', text: 'Application submitted successfully for reviewer assessment!' });
      fetchApplications();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Submission failed.' });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'verified':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800"><CheckCircle2 className="w-3 h-3" /> Verified</span>;
      case 'submitted':
      case 'under review':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800"><Clock className="w-3 h-3" /> {status}</span>;
      case 'flagged':
      case 'needs review':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800"><AlertCircle className="w-3 h-3" /> {status}</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">Draft</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#CBD5E1] pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Scholarship Application Portfolios</h1>
          <p className="text-sm text-[#475569] mt-1">
            Bundle verified certificates into official application portfolios and track reviewer decisions.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          New Application
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-lg text-sm border ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'}`}>
          {message.text}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-[#475569] text-sm">Loading applications...</div>
      ) : applications.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-[#CBD5E1] rounded-xl p-8">
          <FolderCheck className="w-12 h-12 text-[#2563EB] mx-auto mb-3 opacity-60" />
          <h3 className="text-base font-semibold text-[#0F172A]">No Applications Created Yet</h3>
          <p className="text-sm text-[#475569] max-w-md mx-auto mt-1 mb-5">
            Create an application portfolio for your scholarship scheme, attach your verified certificates, and submit for evaluation.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-4 py-2 rounded-lg text-sm font-medium transition"
          >
            <Plus className="w-4 h-4" />
            Create First Application
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5">
          {applications.map((app) => (
            <div key={app.id} className="bg-white border border-[#CBD5E1] rounded-xl p-5 shadow-sm hover:shadow transition">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#2563EB] bg-blue-50 px-2 py-0.5 rounded">
                      {app.application_number}
                    </span>
                    {getStatusBadge(app.status)}
                  </div>
                  <h3 className="text-lg font-bold text-[#0F172A] mt-1.5">{app.title}</h3>
                  <p className="text-xs text-[#475569]">{app.scholarship_name} • Academic Year {app.academic_year}</p>
                </div>

                <div className="flex items-center gap-2">
                  {app.status === 'Draft' && (
                    <>
                      <button
                        onClick={() => setShowAttachModal(app.id)}
                        className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#CBD5E1] text-[#0F172A] hover:bg-slate-50 transition"
                      >
                        <Paperclip className="w-3.5 h-3.5 text-[#2563EB]" />
                        Attach Document
                      </button>
                      <button
                        onClick={() => handleSubmit(app.id)}
                        disabled={app.documents.length === 0}
                        className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg text-white transition ${
                          app.documents.length === 0
                            ? 'bg-slate-300 cursor-not-allowed'
                            : 'bg-emerald-600 hover:bg-emerald-700 shadow-sm'
                        }`}
                      >
                        <Send className="w-3.5 h-3.5" />
                        Submit for Review
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Documents List */}
              <div className="mt-4">
                <div className="text-xs font-semibold text-[#475569] uppercase tracking-wider mb-2">
                  Attached Certificates ({app.documents.length})
                </div>
                {app.documents.length === 0 ? (
                  <div className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                    No documents attached yet. Please attach your verified certificate before submitting.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                    {app.documents.map((doc) => (
                      <div key={doc.id} className="flex items-center gap-2 p-2 rounded-lg bg-[#F8FAFF] border border-slate-100 text-xs">
                        <FileText className="w-4 h-4 text-[#2563EB] shrink-0" />
                        <div className="truncate">
                          <div className="font-semibold text-[#0F172A] truncate">{doc.original_filename}</div>
                          <div className="text-[10px] text-[#475569]">{doc.category}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {app.reviewer_notes && (
                <div className="mt-4 p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs text-[#0F172A]">
                  <span className="font-bold text-[#2563EB]">Reviewer Feedback:</span> {app.reviewer_notes}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-[#CBD5E1]">
            <h3 className="text-lg font-bold text-[#0F172A] mb-4">Create Scholarship Portfolio</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#475569] mb-1">Portfolio Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Post-Matric Merit Scholarship 2026"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#475569] mb-1">Scholarship Scheme</label>
                <select
                  value={newScheme}
                  onChange={(e) => setNewScheme(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                >
                  <option value="National Scholarship Scheme">National Scholarship Scheme (NSP)</option>
                  <option value="State Post-Matric Scholarship">State Post-Matric Scholarship</option>
                  <option value="Merit-cum-Means Scheme">Merit-cum-Means Professional Scheme</option>
                  <option value="AICTE Pragati / Saksham Scheme">AICTE Technical Scheme</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#475569] mb-1">Academic Year</label>
                <input
                  type="text"
                  value={newAcademicYear}
                  onChange={(e) => setNewAcademicYear(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#475569] mb-1">Notes / Instructions</label>
                <textarea
                  rows={3}
                  placeholder="Optional submission remarks..."
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="text-xs px-4 py-2 border border-[#CBD5E1] rounded-lg text-[#475569] hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="text-xs px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-semibold rounded-lg shadow-sm transition"
                >
                  Create Application
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Attach Modal */}
      {showAttachModal !== null && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-[#CBD5E1]">
            <h3 className="text-lg font-bold text-[#0F172A] mb-2">Attach Document</h3>
            <p className="text-xs text-[#475569] mb-4">Select an uploaded certificate to link with this application portfolio.</p>

            {userDocs.length === 0 ? (
              <div className="text-xs text-amber-700 bg-amber-50 p-3 rounded-lg mb-4">
                No uploaded documents found. Please upload a certificate first from the Upload section.
              </div>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto mb-4">
                {userDocs.map((doc) => (
                  <label
                    key={doc.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border text-xs cursor-pointer transition ${
                      selectedDocId === doc.id
                        ? 'border-[#2563EB] bg-blue-50/50'
                        : 'border-[#CBD5E1] hover:bg-slate-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="docSelect"
                      checked={selectedDocId === doc.id}
                      onChange={() => setSelectedDocId(doc.id)}
                      className="text-[#2563EB]"
                    />
                    <div>
                      <div className="font-semibold text-[#0F172A]">{doc.original_filename}</div>
                      <div className="text-[10px] text-[#475569]">{doc.category}</div>
                    </div>
                  </label>
                ))}
              </div>
            )}

            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAttachModal(null)}
                className="text-xs px-4 py-2 border border-[#CBD5E1] rounded-lg text-[#475569] hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!selectedDocId}
                onClick={() => handleAttach(showAttachModal)}
                className="text-xs px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:bg-slate-300 text-white font-semibold rounded-lg shadow-sm transition"
              >
                Confirm Attachment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
