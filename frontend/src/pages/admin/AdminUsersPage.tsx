import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import { Users, FileText, CheckCircle2, Shield } from 'lucide-react';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await api.get('/admin/users');
        setUsers(res.data);
      } catch (err) {
        console.error('Error fetching users:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Registered Users Directory</h1>
        <p className="mt-1 text-xs text-slate-500">
          Overview of all registered students, applicants, and system administrators.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm overflow-x-auto">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading user accounts...</div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">User</th>
                <th className="py-2.5 px-3">Email Address</th>
                <th className="py-2.5 px-3">Role</th>
                <th className="py-2.5 px-3">Uploaded Docs</th>
                <th className="py-2.5 px-3">Verifications Run</th>
                <th className="py-2.5 px-3">Account Status</th>
                <th className="py-2.5 px-3">Joined On</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50">
                  <td className="py-3 px-3 font-semibold text-slate-900 flex items-center gap-2">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-brand-700 font-bold text-xs">
                      {u.full_name?.charAt(0) || u.email.charAt(0).toUpperCase()}
                    </div>
                    <span>{u.full_name || 'Applicant'}</span>
                  </td>
                  <td className="py-3 px-3 text-slate-600 font-mono text-[11px]">{u.email}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize ${
                        u.role === 'admin'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-700 font-medium">{u.document_count || 0}</td>
                  <td className="py-3 px-3 text-slate-700 font-medium">{u.verification_count || 0}</td>
                  <td className="py-3 px-3">
                    {u.is_active ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Active
                      </span>
                    ) : (
                      <span className="text-slate-400">Inactive</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-500">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
