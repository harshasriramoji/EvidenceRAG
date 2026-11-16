import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import { ShieldAlert, CheckCircle2, XCircle, ArrowRight, MessageSquare, ShieldCheck } from 'lucide-react';

export const AdminReviewPage: React.FC = () => {
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIssue, setSelectedIssue] = useState<any | null>(null);
  const [decision, setDecision] = useState<string>('override_pass');
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchReviews = async () => {
    try {
      const res = await api.get('/admin/reviews');
      setReviews(res.data);
    } catch (err) {
      console.error('Error fetching admin reviews:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const handleRecordReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssue) return;

    setSubmitting(true);
    setSuccessMsg(null);
    try {
      await api.post(`/admin/reviews/${selectedIssue.id}`, {
        decision,
        admin_notes: notes,
      });
      setSuccessMsg(`Decision '${decision}' recorded successfully for Issue #${selectedIssue.id}!`);
      setSelectedIssue(null);
      setNotes('');
      fetchReviews();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to record decision.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Manual Review Queue</h1>
        <p className="mt-1 text-xs text-slate-500">
          Inspect compliance issues marked for human discretion, missing signatures, or uncertain OCR findings.
        </p>
      </div>

      {successMsg && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 text-xs font-semibold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          {successMsg}
        </div>
      )}

      {/* Review Dialog/Modal if an issue is selected */}
      {selectedIssue && (
        <div className="rounded-2xl border-2 border-brand-500 bg-white p-6 shadow-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600">
                Recording Decision for Issue #{selectedIssue.id}
              </span>
              <h3 className="text-sm font-bold text-slate-900">{selectedIssue.title}</h3>
            </div>
            <button
              onClick={() => setSelectedIssue(null)}
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              Cancel
            </button>
          </div>

          <div className="text-xs text-slate-600 space-y-1 bg-slate-50 p-3 rounded-xl border border-slate-200">
            <div><span className="font-semibold text-slate-900">Document:</span> {selectedIssue.document_name}</div>
            <div><span className="font-semibold text-slate-900">Snippet:</span> "{selectedIssue.evidence_snippet}"</div>
            <div><span className="font-semibold text-slate-900">Explanation:</span> {selectedIssue.explanation}</div>
          </div>

          <form onSubmit={handleRecordReview} className="space-y-3 pt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-1">
                Official Administrative Decision:
              </label>
              <select
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
                className="w-full rounded-lg border border-slate-300 py-2 px-3 text-xs text-slate-900 focus:border-brand-500 focus:outline-none bg-white"
              >
                <option value="override_pass">Override & Pass (Accept Document as Genuine)</option>
                <option value="requires_resubmission">Requires Resubmission (Notify Applicant to Re-upload)</option>
                <option value="approved">Approved (Compliance Validated)</option>
                <option value="rejected">Rejected (Irreparable Disqualification)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-1">
                Administrative Notes & Justification:
              </label>
              <textarea
                rows={3}
                required
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Inspected visual seal under high magnification; document is authentic despite OCR low contrast."
                className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-900 focus:border-brand-500 focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedIssue(null)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="rounded-lg bg-brand-600 px-5 py-2 text-xs font-semibold text-white shadow hover:bg-brand-700 disabled:opacity-50"
              >
                {submitting ? 'Recording...' : 'Save Decision in Database'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Flagged Issues List */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading flagged queue...</div>
        ) : reviews.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {reviews.map((iss) => (
              <div key={iss.id} className="py-4 first:pt-0 last:pb-0 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-slate-900">Issue #{iss.id}</span>
                    <span className="rounded bg-rose-50 px-2 py-0.5 text-[10px] font-semibold text-rose-700 border border-rose-200 uppercase">
                      {iss.severity}
                    </span>
                    <span className="font-semibold text-xs text-slate-800">{iss.title}</span>
                  </div>

                  <p className="text-xs text-slate-600">
                    <span className="font-medium text-slate-700">Document: </span>
                    {iss.document_name}
                  </p>

                  <p className="text-xs text-slate-500 line-clamp-2 max-w-2xl font-mono text-[11px]">
                    "{iss.evidence_snippet}"
                  </p>

                  {iss.admin_review ? (
                    <div className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-800 border border-emerald-200">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                      Decision: {iss.admin_review.decision} ("{iss.admin_review.admin_notes}")
                    </div>
                  ) : (
                    <div className="mt-1 text-[11px] font-semibold text-amber-600">
                      Pending Officer Decision
                    </div>
                  )}
                </div>

                <div className="shrink-0">
                  <button
                    onClick={() => {
                      setSelectedIssue(iss);
                      setNotes(iss.admin_review?.admin_notes || '');
                      setDecision(iss.admin_review?.decision || 'override_pass');
                    }}
                    className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-slate-800 transition-colors"
                  >
                    <ShieldCheck className="h-4 w-4" />
                    {iss.admin_review ? 'Update Decision' : 'Review & Decide'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-slate-500">
            <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500 mb-2" />
            <p className="font-medium text-slate-700">The manual review queue is clear!</p>
            <p className="mt-1">No pending issues flagged for human discretion.</p>
          </div>
        )}
      </div>
    </div>
  );
};
