import React, { useState, useEffect } from 'react';
import { HelpCircle, Send, MessageSquare, CheckCircle, Clock, Plus, AlertCircle } from 'lucide-react';
import api from '../api/client';

interface Ticket {
  id: number;
  ticket_number: string;
  subject: string;
  category: string;
  priority: string;
  status: string;
  message: string;
  admin_reply?: string;
  created_at: string;
}

export const SupportPage: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('Verification Question');
  const [priority, setPriority] = useState('Medium');
  const [userMessage, setUserMessage] = useState('');
  const [toast, setToast] = useState<string | null>(null);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const res = await api.get('/support');
      setTickets(res.data);
    } catch (err) {
      console.error('Failed to load tickets', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/support', {
        subject,
        category,
        priority,
        message: userMessage
      });
      setToast('Support ticket submitted successfully!');
      setShowCreate(false);
      setSubject('');
      setUserMessage('');
      fetchTickets();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit ticket');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#CBD5E1] pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Help & Support Inquiries</h1>
          <p className="text-sm text-[#475569] mt-1">
            Submit clarification questions regarding rejected certificates, statutory guidelines, or system errors.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          New Inquiry Ticket
        </button>
      </div>

      {toast && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-semibold">
          {toast}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-[#475569] text-sm">Loading tickets...</div>
      ) : tickets.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-[#CBD5E1] rounded-xl p-8">
          <HelpCircle className="w-12 h-12 text-[#2563EB] mx-auto mb-3 opacity-60" />
          <h3 className="text-base font-semibold text-[#0F172A]">No Support Inquiries</h3>
          <p className="text-sm text-[#475569] max-w-md mx-auto mt-1 mb-5">
            If you have questions about document verification errors or scholarship eligibility requirements, open an inquiry ticket.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-4 py-2 rounded-lg text-sm font-medium transition"
          >
            <Plus className="w-4 h-4" />
            Open Support Ticket
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {tickets.map((t) => (
            <div key={t.id} className="bg-white border border-[#CBD5E1] rounded-xl p-5 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-[#2563EB] bg-blue-50 px-2 py-0.5 rounded">
                    {t.ticket_number}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                    t.priority === 'High' ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-700'
                  }`}>
                    {t.priority}
                  </span>
                  <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded ${
                    t.status === 'Resolved' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {t.status === 'Resolved' ? <CheckCircle className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                    {t.status}
                  </span>
                </div>
                <div className="text-[11px] text-[#475569]">{new Date(t.created_at).toLocaleDateString()}</div>
              </div>

              <div className="mt-3">
                <h4 className="text-sm font-bold text-[#0F172A]">{t.subject}</h4>
                <div className="text-xs text-[#475569] mt-0.5 font-medium">{t.category}</div>
                <p className="text-xs text-slate-700 mt-2 bg-[#F8FAFF] p-3 rounded-lg border border-slate-100 leading-relaxed">
                  {t.message}
                </p>
              </div>

              {t.admin_reply && (
                <div className="mt-4 p-3.5 rounded-lg bg-blue-50/70 border border-blue-200">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#2563EB] mb-1">
                    <MessageSquare className="w-3.5 h-3.5" />
                    Official Support Response
                  </div>
                  <p className="text-xs text-[#0F172A] leading-relaxed">
                    {t.admin_reply}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-[#CBD5E1]">
            <h3 className="text-lg font-bold text-[#0F172A] mb-4">Open Support Inquiry</h3>
            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#475569] mb-1">Subject</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Income Certificate Expired Flag Explanation"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#475569] mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                  >
                    <option value="Verification Question">Verification Question</option>
                    <option value="Guideline Clarification">Guideline Clarification</option>
                    <option value="Document Upload Issue">Document Upload Issue</option>
                    <option value="System Feedback">System Feedback</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#475569] mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#475569] mb-1">Detailed Message</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Explain your inquiry or issue with certificate details..."
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="text-xs px-4 py-2 border border-[#CBD5E1] rounded-lg text-[#475569] hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="text-xs px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-semibold rounded-lg shadow-sm transition"
                >
                  Submit Inquiry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
