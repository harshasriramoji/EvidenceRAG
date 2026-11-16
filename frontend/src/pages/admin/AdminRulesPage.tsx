import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import { Settings, Plus, CheckCircle2, Edit3, X, Sliders } from 'lucide-react';

export const AdminRulesPage: React.FC = () => {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingRule, setEditingRule] = useState<any | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [validityMonths, setValidityMonths] = useState<number>(0);
  const [mandatoryFieldsStr, setMandatoryFieldsStr] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const fetchRules = async () => {
    try {
      const res = await api.get('/admin/rules');
      setRules(res.data);
    } catch (err) {
      console.error('Error fetching verification rules:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const openEdit = (rule: any) => {
    setEditingRule(rule);
    setName(rule.name);
    setDescription(rule.description);
    setValidityMonths(rule.validity_period_months || 0);
    setMandatoryFieldsStr((rule.mandatory_fields || []).join(', '));
    setMsg(null);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRule) return;

    setSaving(true);
    setMsg(null);
    try {
      const parsedFields = mandatoryFieldsStr
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      await api.put(`/admin/rules/${editingRule.id}`, {
        name,
        description,
        validity_period_months: validityMonths,
        mandatory_fields: parsedFields,
      });

      setMsg(`Rule '${editingRule.rule_code}' successfully updated!`);
      setEditingRule(null);
      fetchRules();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update rule.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Verification Rules Engine</h1>
          <p className="mt-1 text-xs text-slate-500">
            Configure mandatory attributes, expiration thresholds, and regulatory compliance constraints per category.
          </p>
        </div>
      </div>

      {msg && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 text-xs font-semibold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          {msg}
        </div>
      )}

      {/* Edit Rule Card */}
      {editingRule && (
        <div className="rounded-2xl border-2 border-brand-500 bg-white p-6 shadow-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600">
                Editing Rule: {editingRule.rule_code}
              </span>
              <h3 className="text-sm font-bold text-slate-900">{editingRule.document_category}</h3>
            </div>
            <button
              onClick={() => setEditingRule(null)}
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <form onSubmit={handleSave} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Rule Title</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-900 focus:border-brand-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Regulatory Description</label>
              <textarea
                rows={2}
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-900 focus:border-brand-500 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Validity Period (Months, 0 = Permanent)
                </label>
                <input
                  type="number"
                  min={0}
                  max={120}
                  value={validityMonths}
                  onChange={(e) => setValidityMonths(parseInt(e.target.value) || 0)}
                  className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-900 focus:border-brand-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mandatory Fields (comma-separated)
                </label>
                <input
                  type="text"
                  value={mandatoryFieldsStr}
                  onChange={(e) => setMandatoryFieldsStr(e.target.value)}
                  placeholder="e.g. full_name, dob, annual_income"
                  className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-900 focus:border-brand-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingRule(null)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-brand-600 px-5 py-2 text-xs font-semibold text-white shadow hover:bg-brand-700 disabled:opacity-50"
              >
                {saving ? 'Updating...' : 'Save Rule Configuration'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Rules Table */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm overflow-x-auto">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading rules...</div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Rule Code</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Validity Window</th>
                <th className="py-2.5 px-3">Mandatory Fields</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50">
                  <td className="py-3 px-3 font-mono font-semibold text-brand-700">{r.rule_code}</td>
                  <td className="py-3 px-3 font-medium text-slate-900">{r.document_category}</td>
                  <td className="py-3 px-3 text-slate-600">
                    {r.validity_period_months === 0 ? (
                      <span className="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700">Permanent</span>
                    ) : (
                      <span className="rounded bg-amber-50 px-2 py-0.5 font-medium text-amber-800 border border-amber-200">
                        {r.validity_period_months} Months
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-600">
                    <div className="flex flex-wrap gap-1 max-w-sm">
                      {r.mandatory_fields?.map((f: string) => (
                        <span key={f} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-700 font-mono">
                          {f}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => openEdit(r)}
                      className="inline-flex items-center gap-1 rounded bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-200"
                    >
                      <Edit3 className="h-3 w-3" /> Edit
                    </button>
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
