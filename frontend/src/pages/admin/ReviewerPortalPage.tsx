import React, { useState, useEffect } from 'react';
import { ShieldCheck, Check, X, AlertTriangle, HelpCircle, FileText, ChevronRight, User, Clock, Building } from 'lucide-react';
import api from '../../api/client';

interface FlaggedIssue {
  id: number;
  document_name: string;
  page_number: number;
  title: string;
  category: string;
  severity: string;
  evidence_snippet?: string;
  expected_value?: string;
  actual_value?: string;
  explanation: string;
  rag_rule_id?: string;
  suggested_correction?: string;
  review_status: string;
}

interface PendingApplication {
  id: number;
  application_number: string;
  title: string;
  scholarship_name: string;
  applicant_id: number;
  status: string;
  academic_year: string;
  notes?: string;
  submitted_at?: string;
  documents: Array<{
    id: number;
    filename: string;
    original_filename: string;
    category: string;
    upload_status: string;
  }>;
}

export const ReviewerPortalPage: React.FC = () => {
  const [issues, setIssues] = useState<FlaggedIssue[]>([]);
  const [applications, setApplications] = useState<PendingApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'issues' | 'applications'>('issues');
  const [reviewerComment, setReviewerComment] = useState<{ [key: number]: string }>({});
  const [toast, setToast] = useState<string | null>(null);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const res = await api.get('/reviews/queue');
      setIssues(res.data.flagged_issues || []);
      setApplications(res.data.pending_applications || []);
    } catch (err) {
      console.error('Failed to load reviewer queue', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleIssueDecision = async (issueId: number, decision: string) => {
    try {
      const comment = reviewerComment[issueId] || '';
      await api.post(`/reviews/issues/${issueId}/decision`, {
        decision,
        reviewer_comments: comment || `Reviewer marked finding as ${decision}.`
      });
      setToast(`Issue #${issueId} decision recorded: ${decision.toUpperCase()}`);
      fetchQueue();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit decision');
    }
  };

  const handleApplicationStatus = async (appId: number, status: string) => {
    try {
      const notes = prompt(`Enter optional reviewer notes for marking this application as ${status}:`) || undefined;
      await api.put(`/reviews/applications/${appId}/status`, {
        status,
        reviewer_notes: notes
      });
      setToast(`Application status updated to: ${status}`);
      fetchQueue();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update application');
    }
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-[#CBD5E1] pb-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Human Reviewer Workspace</h1>
          <p className="text-sm text-[#475569] mt-1">
            Human-in-the-Loop decision station to inspect flagged AI findings, override passes, and approve applications.
          </p>
        </div>

        <div className="flex rounded-lg border border-[#CBD5E1] p-1 bg-white text-xs font-semibold">
          <button
            onClick={() => setActiveTab('issues')}
            className={`px-3 py-1.5 rounded-md transition ${
              activeTab === 'issues' ? 'bg-[#2563EB] text-white shadow-sm' : 'text-[#475569] hover:text-[#0F172A]'
            }`}
          >
            Flagged AI Findings ({issues.length})
          </button>
          <button
            onClick={() => setActiveTab('applications')}
            className={`px-3 py-1.5 rounded-md transition ${
              activeTab === 'applications' ? 'bg-[#2563EB] text-white shadow-sm' : 'text-[#475569] hover:text-[#0F172A]'
            }`}
          >
            Submitted Portfolios ({applications.length})
          </button>
        </div>
      </div>

      {toast && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-semibold">
          {toast}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-[#475569] text-sm">Loading review queue...</div>
      ) : activeTab === 'issues' ? (
        issues.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-[#CBD5E1] p-6 text-[#475569] text-sm">
            <ShieldCheck className="w-10 h-10 text-emerald-500 mx-auto mb-2 opacity-80" />
            No flagged issues requiring manual evaluation at this time.
          </div>
        ) : (
          <div className="space-y-4">
            {issues.map((iss) => (
              <div key={iss.id} className="bg-white border border-[#CBD5E1] rounded-xl p-5 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold bg-amber-50 text-amber-800 px-2 py-0.5 rounded">
                      Issue #{iss.id}
                    </span>
                    <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded uppercase">
                      {iss.severity}
                    </span>
                    <span className="text-xs text-[#475569]">• {iss.document_name} (Page {iss.page_number})</span>
                  </div>
                  <div className="text-xs font-semibold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded">
                    Status: {iss.review_status}
                  </div>
                </div>

                <div className="mt-3">
                  <h3 className="text-base font-bold text-[#0F172A]">{iss.title}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2 text-xs bg-[#F8FAFF] p-3 rounded-lg border border-slate-100">
                    <div>
                      <span className="font-semibold text-[#475569]">Expected Standard:</span>{' '}
                      <span className="text-slate-800 font-mono">{iss.expected_value || 'Compliant with policy'}</span>
                    </div>
                    <div>
                      <span className="font-semibold text-[#475569]">Detected in Evidence:</span>{' '}
                      <span className="text-slate-800 font-mono">{iss.actual_value || 'Discrepancy detected'}</span>
                    </div>
                  </div>

                  {iss.explanation && (
                    <div className="mt-3 text-xs text-slate-700 leading-relaxed">
                      <span className="font-bold text-[#0F172A]">AI Explanation & Policy Grounding:</span> {iss.explanation}
                    </div>
                  )}

                  {iss.rag_rule_id && (
                    <div className="mt-1 text-[11px] font-mono text-[#2563EB]">
                      Statutory Basis: {iss.rag_rule_id}
                    </div>
                  )}
                </div>

                {/* Reviewer Actions */}
                <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <input
                    type="text"
                    placeholder="Enter reviewer remark (optional)..."
                    value={reviewerComment[iss.id] || ''}
                    onChange={(e) => setReviewerComment({ ...reviewerComment, [iss.id]: e.target.value })}
                    className="flex-1 text-xs px-3 py-1.5 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                  />
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleIssueDecision(iss.id, 'override_pass')}
                      className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Override Pass
                    </button>
                    <button
                      onClick={() => handleIssueDecision(iss.id, 'rejected')}
                      className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 transition"
                    >
                      <X className="w-3.5 h-3.5" />
                      Confirm Issue
                    </button>
                    <button
                      onClick={() => handleIssueDecision(iss.id, 'request_info')}
                      className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition"
                    >
                      <HelpCircle className="w-3.5 h-3.5" />
                      Request Info
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      ) : applications.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-[#CBD5E1] p-6 text-[#475569] text-sm">
          No submitted student applications currently pending reviewer evaluation.
        </div>
      ) : (
        <div className="space-y-4">
          {applications.map((app) => (
            <div key={app.id} className="bg-white border border-[#CBD5E1] rounded-xl p-5 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold bg-blue-50 text-[#2563EB] px-2 py-0.5 rounded">
                      {app.application_number}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                      {app.status}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-[#0F172A] mt-1">{app.title}</h3>
                  <div className="text-xs text-[#475569]">Applicant ID: #{app.applicant_id} • {app.scholarship_name}</div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleApplicationStatus(app.id, 'Verified')}
                    className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Approve & Verify
                  </button>
                  <button
                    onClick={() => handleApplicationStatus(app.id, 'Needs Review')}
                    className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white shadow-sm transition"
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Needs Review
                  </button>
                </div>
              </div>

              {/* Certificates */}
              <div className="mt-3">
                <div className="text-xs font-semibold text-[#475569] uppercase tracking-wider mb-2">
                  Submitted Documents ({app.documents.length})
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                  {app.documents.map((d) => (
                    <div key={d.id} className="p-2.5 rounded-lg bg-[#F8FAFF] border border-slate-100 flex items-center gap-2 text-xs">
                      <FileText className="w-4 h-4 text-[#2563EB]" />
                      <div className="truncate">
                        <div className="font-semibold text-[#0F172A] truncate">{d.original_filename}</div>
                        <div className="text-[10px] text-[#475569]">{d.category}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
