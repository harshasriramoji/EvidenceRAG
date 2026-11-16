import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import {
  Shield,
  Search,
  Filter,
  RefreshCw,
  Clock,
  User,
  Activity,
  FileText,
  Sliders,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

interface AuditLogItem {
  id: number;
  user_id: number | null;
  user_email: string;
  action: string;
  target_type: string | null;
  target_id: number | null;
  details: string | null;
  ip_address: string;
  timestamp: string;
}

export const AdminAuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAction, setSelectedAction] = useState<string>('All');

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/audit-logs');
      setLogs(res.data || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  const actionTypes = ['All', 'ADMIN_REVIEW_DECISION', 'UPLOAD_NEW_VERSION', 'ADD_REFERENCE_MATERIAL', 'UPDATE_RULE'];

  const filteredLogs = logs.filter((l) => {
    const matchesAction = selectedAction === 'All' || l.action === selectedAction;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      l.user_email.toLowerCase().includes(q) ||
      (l.details || '').toLowerCase().includes(q) ||
      l.action.toLowerCase().includes(q) ||
      (l.target_type || '').toLowerCase().includes(q);
    return matchesAction && matchesSearch;
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-purple-600" />
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Administrative Audit Trail</h1>
          </div>
          <p className="mt-1 text-xs text-[#475569]">
            Tamper-resistant historical audit logs recording administrative review decisions, verification rule revisions, and document updates.
          </p>
        </div>

        <button
          onClick={fetchAuditLogs}
          className="flex items-center gap-1.5 rounded-lg border border-[#CBD5E1] bg-white px-3.5 py-2 text-xs font-semibold text-[#0F172A] hover:bg-slate-50 cursor-pointer self-start sm:self-center"
        >
          <RefreshCw className="h-3.5 w-3.5 text-[#475569]" /> Refresh Trail
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-xs">
          <div className="text-[11px] font-semibold text-[#475569] uppercase">Total Logged Events</div>
          <div className="mt-2 text-2xl font-bold text-[#0F172A]">{logs.length}</div>
          <div className="mt-1 text-[11px] text-emerald-600 font-medium flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" /> Immutably Persisted
          </div>
        </div>

        <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-xs">
          <div className="text-[11px] font-semibold text-[#475569] uppercase">Review Decisions</div>
          <div className="mt-2 text-2xl font-bold text-purple-700">
            {logs.filter((l) => l.action === 'ADMIN_REVIEW_DECISION').length}
          </div>
          <div className="mt-1 text-[11px] text-[#475569]">Staff override actions</div>
        </div>

        <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-xs">
          <div className="text-[11px] font-semibold text-[#475569] uppercase">Document Revisions</div>
          <div className="mt-2 text-2xl font-bold text-[#2563EB]">
            {logs.filter((l) => l.action === 'UPLOAD_NEW_VERSION').length}
          </div>
          <div className="mt-1 text-[11px] text-[#475569]">Student re-submissions</div>
        </div>

        <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-xs">
          <div className="text-[11px] font-semibold text-[#475569] uppercase">Policy Revisions</div>
          <div className="mt-2 text-2xl font-bold text-amber-700">
            {logs.filter((l) => l.action.includes('RULE') || l.action.includes('REFERENCE')).length}
          </div>
          <div className="mt-1 text-[11px] text-[#475569]">Knowledge updates</div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="rounded-2xl border border-[#CBD5E1] bg-white p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#475569]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search audit trail by actor email, details, target..."
              className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 pl-9 pr-3 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            {actionTypes.map((act) => (
              <button
                key={act}
                onClick={() => setSelectedAction(act)}
                className={`rounded-lg px-2.5 py-1 font-semibold whitespace-nowrap cursor-pointer transition-colors ${
                  selectedAction === act
                    ? 'bg-purple-700 text-white shadow-xs'
                    : 'bg-white border border-[#CBD5E1] text-[#475569] hover:bg-slate-50'
                }`}
              >
                {act.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Audit Log Table */}
        {loading ? (
          <div className="p-8 text-center text-xs text-[#475569]">Loading audit records...</div>
        ) : filteredLogs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#EFF6FF] text-[#1D4ED8] uppercase tracking-wider font-semibold border-b border-blue-200">
                <tr>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Actor Email</th>
                  <th className="py-2.5 px-3">Action Type</th>
                  <th className="py-2.5 px-3">Target Reference</th>
                  <th className="py-2.5 px-3">Audit Details & Justification</th>
                  <th className="py-2.5 px-3">Client Host</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="py-3 px-3 font-mono text-[11px] text-[#475569] whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 font-semibold text-[#0F172A]">
                      {log.user_email}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          log.action.includes('ADMIN')
                            ? 'bg-purple-100 text-purple-800'
                            : log.action.includes('VERSION')
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-700">
                      {log.target_type ? `${log.target_type} #${log.target_id || ''}` : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-[11px] text-[#0F172A] max-w-sm">
                      {log.details || 'Action completed successfully.'}
                    </td>
                    <td className="py-3 px-3 font-mono text-[10px] text-slate-400">
                      {log.ip_address}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-[#475569]">
            No audit log entries matched your filter.
          </div>
        )}
      </div>
    </div>
  );
};
