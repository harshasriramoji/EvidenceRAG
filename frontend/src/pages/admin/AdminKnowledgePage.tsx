import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import {
  BookOpen,
  Search,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Sliders,
  Plus,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Send,
  Edit3,
  X,
  Clock,
  Layers,
  HelpCircle,
  Cpu
} from 'lucide-react';

interface KnowledgeRule {
  id: string;
  category: string;
  title: string;
  content: string;
  source: string;
  mandatory_fields: string[];
  validity_months: number;
  similarity_score?: number;
}

interface TestQueryResponse {
  query: string;
  category_filter?: string;
  retrieved_rules: Array<{
    rule_id: string;
    category: string;
    title: string;
    content: string;
    source: string;
    similarity_score: number;
  }>;
  rag_preview: {
    explanation: string;
    suggested_correction: string;
    rag_rule_id?: string;
    rag_source?: string;
    llm_used?: boolean;
    model_name?: string;
  };
}

export const AdminKnowledgePage: React.FC = () => {
  const [rules, setRules] = useState<KnowledgeRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  // Test RAG Retrieval state
  const [testQuery, setTestQuery] = useState('Income certificate issued 2 years ago, is it acceptable?');
  const [testCategory, setTestCategory] = useState<string>('');
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<TestQueryResponse | null>(null);

  // Modal State for Add / Edit Rule
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<KnowledgeRule | null>(null);
  const [formData, setFormData] = useState({
    id: '',
    category: 'Income Certificate',
    title: '',
    content: '',
    source: '',
    mandatory_fields: '',
    validity_months: 12
  });
  const [savingRule, setSavingRule] = useState(false);

  const fetchKnowledgeRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/admin/knowledge-base');
      setRules(res.data.rules || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load RAG knowledge base rules.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKnowledgeRules();
  }, []);

  const handleTestQuery = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!testQuery.trim()) return;

    setTestLoading(true);
    try {
      const payload: Record<string, any> = { query: testQuery.trim(), top_k: 2 };
      if (testCategory) payload.category = testCategory;
      const res = await api.post('/admin/knowledge-base/test-query', payload);
      setTestResult(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to execute semantic query test.');
    } finally {
      setTestLoading(false);
    }
  };

  const handleOpenAddModal = () => {
    setEditingRule(null);
    setFormData({
      id: `KB-RULE-${String(rules.length + 1).padStart(3, '0')}`,
      category: 'General Quality',
      title: '',
      content: '',
      source: '',
      mandatory_fields: '',
      validity_months: 0
    });
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (rule: KnowledgeRule) => {
    setEditingRule(rule);
    setFormData({
      id: rule.id,
      category: rule.category,
      title: rule.title,
      content: rule.content,
      source: rule.source,
      mandatory_fields: (rule.mandatory_fields || []).join(', '),
      validity_months: rule.validity_months || 0
    });
    setIsModalOpen(true);
  };

  const handleSaveRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingRule(true);
    try {
      const fieldsArray = formData.mandatory_fields
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const payload = {
        category: formData.category,
        title: formData.title,
        content: formData.content,
        source: formData.source,
        mandatory_fields: fieldsArray,
        validity_months: Number(formData.validity_months)
      };

      if (editingRule) {
        await api.put(`/admin/knowledge-base/${editingRule.id}`, payload);
      } else {
        await api.post('/admin/knowledge-base', { id: formData.id, ...payload });
      }

      setIsModalOpen(false);
      fetchKnowledgeRules();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save rule.');
    } finally {
      setSavingRule(false);
    }
  };

  const categories = ['All', ...Array.from(new Set(rules.map((r) => r.category)))];

  const filteredRules = rules.filter((r) => {
    const matchesCategory = selectedCategory === 'All' || r.category === selectedCategory;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      r.title.toLowerCase().includes(q) ||
      r.content.toLowerCase().includes(q) ||
      r.category.toLowerCase().includes(q) ||
      r.source.toLowerCase().includes(q) ||
      r.id.toLowerCase().includes(q);
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
              RAG Reference Knowledge Base
            </h1>
            <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-[#2563EB]">
              Explainable AI
            </span>
          </div>
          <p className="mt-1 text-xs text-[#475569]">
            Regulatory verification rules and statutory norms queried by the RAG engine to explain application document issues.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchKnowledgeRules}
            className="flex items-center gap-1.5 rounded-lg border border-[#CBD5E1] bg-white px-3 py-1.5 text-xs font-semibold text-[#0F172A] hover:bg-slate-50 cursor-pointer transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5 text-[#475569]" />
            Refresh Rules
          </button>
          <button
            onClick={handleOpenAddModal}
            className="flex items-center gap-1.5 rounded-lg bg-[#2563EB] px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-[#1D4ED8] cursor-pointer transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Policy Rule
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-[#475569] uppercase tracking-wider">
            Total Regulatory Rules
          </div>
          <div className="mt-2 text-2xl font-bold text-[#0F172A]">{rules.length}</div>
          <div className="mt-1 text-[11px] text-emerald-600 font-medium flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" />
            All Policy Rules Active
          </div>
        </div>

        <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-[#475569] uppercase tracking-wider">
            Document Categories
          </div>
          <div className="mt-2 text-2xl font-bold text-[#0F172A]">{categories.length - 1}</div>
          <div className="mt-1 text-[11px] text-[#475569]">Identity, Income, Caste, Bank, etc.</div>
        </div>

        <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-[#475569] uppercase tracking-wider">
            Semantic Vector Index
          </div>
          <div className="mt-2 text-2xl font-bold text-[#2563EB]">TF-IDF + Cosine</div>
          <div className="mt-1 text-[11px] text-[#475569]">Indexed & Cached in Memory</div>
        </div>

        <div className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-[#475569] uppercase tracking-wider">
            RAG Generator Mode
          </div>
          <div className="mt-2 text-xl font-bold text-purple-700 flex items-center gap-1.5">
            <Cpu className="h-5 w-5" />
            <span>Hybrid Ollama / Fallback</span>
          </div>
          <div className="mt-1 text-[11px] text-[#475569]">Deterministic Grounded Guardrails</div>
        </div>
      </div>

      {/* Interactive Semantic RAG Tester Card */}
      <div className="rounded-2xl border border-blue-200 bg-gradient-to-r from-blue-50/50 via-white to-purple-50/30 p-5 shadow-sm">
        <div className="flex items-center gap-2 text-sm font-bold text-[#0F172A] mb-1">
          <Sparkles className="h-4 w-4 text-[#2563EB]" />
          <span>Interactive RAG Semantic Retrieval & Grounding Tester</span>
        </div>
        <p className="text-xs text-[#475569] mb-4">
          Test how the RAG engine searches across all regulatory policies to locate relevant evidence and draft automated, citation-grounded student feedback.
        </p>

        <form onSubmit={handleTestQuery} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="md:col-span-3">
              <input
                type="text"
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                placeholder="Enter an issue or scenario (e.g., 'Aadhaar DOB is cut off' or 'Income cert is over 1 year old')"
                className="w-full rounded-lg border border-[#CBD5E1] bg-white px-3 py-2 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
              />
            </div>
            <div>
              <select
                value={testCategory}
                onChange={(e) => setTestCategory(e.target.value)}
                className="w-full rounded-lg border border-[#CBD5E1] bg-white px-3 py-2 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
              >
                <option value="">Any Document Category</option>
                {categories
                  .filter((c) => c !== 'All')
                  .map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-[11px] text-[#475569]">
              Live evaluation using vectorized statutory embeddings and semantic ranking.
            </div>
            <button
              type="submit"
              disabled={testLoading || !testQuery.trim()}
              className="flex items-center gap-1.5 rounded-lg bg-[#2563EB] px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-[#1D4ED8] disabled:opacity-50 cursor-pointer transition-colors"
            >
              {testLoading ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Retrieving...
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  Run Semantic Retrieval
                </>
              )}
            </button>
          </div>
        </form>

        {/* Live Test Query Result Display */}
        {testResult && (
          <div className="mt-5 rounded-xl border border-blue-200 bg-white p-4 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                Retrieved {testResult.retrieved_rules.length} Relevant Policy Rules
              </span>
              <span className="text-[10px] font-mono text-[#475569]">
                RAG Engine: {testResult.rag_preview.llm_used ? 'Ollama LLM' : 'Deterministic Grounded Guardrail'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Left Column: Top Matched Rule */}
              {testResult.retrieved_rules.length > 0 && (
                <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-[#2563EB]">
                      {testResult.retrieved_rules[0].rule_id}
                    </span>
                    <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                      Match: {(testResult.retrieved_rules[0].similarity_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-xs font-bold text-[#0F172A]">
                    {testResult.retrieved_rules[0].title}
                  </div>
                  <p className="text-[11px] text-[#475569] leading-relaxed">
                    {testResult.retrieved_rules[0].content}
                  </p>
                  <div className="text-[10px] text-slate-500 italic pt-1 border-t border-slate-200">
                    Authority: {testResult.retrieved_rules[0].source}
                  </div>
                </div>
              )}

              {/* Right Column: Generated Grounded Explanation & Correction */}
              <div className="rounded-lg border border-purple-200 bg-purple-50/40 p-3 space-y-2.5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-purple-900">
                  <Sparkles className="h-3.5 w-3.5 text-purple-600" />
                  <span>Synthesized Explainable Output</span>
                </div>
                <div>
                  <div className="text-[10px] font-semibold text-purple-900 uppercase">
                    Grounded Explanation:
                  </div>
                  <p className="text-[11px] text-[#0F172A] mt-0.5 leading-relaxed bg-white/80 p-2 rounded border border-purple-100">
                    {testResult.rag_preview.explanation}
                  </p>
                </div>
                <div>
                  <div className="text-[10px] font-semibold text-emerald-900 uppercase">
                    Recommended Student Action:
                  </div>
                  <p className="text-[11px] text-[#0F172A] mt-0.5 leading-relaxed bg-white/80 p-2 rounded border border-emerald-100">
                    {testResult.rag_preview.suggested_correction}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Policy Rules Directory & Filtering */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#475569]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search policies by keyword, regulation, category..."
              className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 pl-9 pr-3 text-xs text-[#0F172A] placeholder:text-[#475569]/60 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
            />
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-lg px-2.5 py-1 font-semibold whitespace-nowrap cursor-pointer transition-colors ${
                  selectedCategory === cat
                    ? 'bg-[#2563EB] text-white shadow-xs'
                    : 'bg-white border border-[#CBD5E1] text-[#475569] hover:bg-slate-50'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Rules Cards List */}
        {loading ? (
          <div className="rounded-xl border border-[#CBD5E1] bg-white p-12 text-center text-xs text-[#475569]">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto text-[#2563EB] mb-2" />
            Loading regulatory knowledge base rules...
          </div>
        ) : filteredRules.length === 0 ? (
          <div className="rounded-xl border border-[#CBD5E1] bg-white p-12 text-center text-xs text-[#475569]">
            No knowledge rules matched your search query.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredRules.map((rule) => (
              <div
                key={rule.id}
                className="rounded-xl border border-[#CBD5E1] bg-white p-4 shadow-xs hover:border-[#2563EB]/50 transition-all flex flex-col justify-between"
              >
                <div className="space-y-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="rounded bg-blue-50 border border-blue-200 px-2 py-0.5 text-[10px] font-bold text-[#2563EB]">
                        {rule.id}
                      </span>
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                        {rule.category}
                      </span>
                      {rule.validity_months > 0 ? (
                        <span className="rounded bg-amber-50 border border-amber-200 px-1.5 py-0.5 text-[10px] font-medium text-amber-800 flex items-center gap-1">
                          <Clock className="h-2.5 w-2.5" />
                          Valid: {rule.validity_months} Mos
                        </span>
                      ) : (
                        <span className="rounded bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 text-[10px] font-medium text-emerald-800">
                          Permanent
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleOpenEditModal(rule)}
                      className="p-1 text-slate-400 hover:text-[#2563EB] hover:bg-blue-50 rounded cursor-pointer"
                      title="Edit rule"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <h3 className="text-sm font-bold text-[#0F172A]">{rule.title}</h3>

                  <p className="text-xs text-[#475569] leading-relaxed">
                    {rule.content}
                  </p>

                  {/* Mandatory Fields */}
                  {rule.mandatory_fields && rule.mandatory_fields.length > 0 && (
                    <div className="pt-1">
                      <span className="text-[10px] font-semibold text-[#0F172A] uppercase tracking-wider block mb-1">
                        Mandatory Required Fields:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {rule.mandatory_fields.map((f) => (
                          <span
                            key={f}
                            className="font-mono text-[10px] bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded border border-slate-200"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
                  <div className="text-[10px] text-slate-500 truncate max-w-[240px]" title={rule.source}>
                    <span className="font-semibold text-slate-700">Source:</span> {rule.source}
                  </div>
                  <button
                    onClick={() => {
                      setTestQuery(`Verify compliance with: ${rule.title}`);
                      setTestCategory(rule.category);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    className="text-[#2563EB] hover:underline font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    Test RAG <ExternalLink className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit / Add Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-[#CBD5E1] space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-[#0F172A]">
                {editingRule ? `Edit Policy Rule: ${editingRule.id}` : 'Add New Regulatory Verification Rule'}
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSaveRule} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#0F172A] mb-1">Rule ID</label>
                  <input
                    type="text"
                    disabled={!!editingRule}
                    value={formData.id}
                    onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                    className="w-full rounded-lg border border-[#CBD5E1] bg-slate-50 py-2 px-3 text-xs font-mono text-[#0F172A]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0F172A] mb-1">Category</label>
                  <input
                    type="text"
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g., Income Certificate"
                    className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">Rule Title</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g., Income Certificate Validity & Limits"
                  className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Full Policy Content / Verification Requirements
                </label>
                <textarea
                  rows={4}
                  required
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="Describe the exact requirements, criteria, formatting guidelines, and statutory rules..."
                  className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Regulatory & Legal Citation Source
                </label>
                <input
                  type="text"
                  required
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  placeholder="e.g., State Revenue Department Circular & NSP Clause 4.2"
                  className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                    Mandatory Fields (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.mandatory_fields}
                    onChange={(e) => setFormData({ ...formData, mandatory_fields: e.target.value })}
                    placeholder="full_name, dob, cert_no"
                    className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs font-mono text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                    Validity Period (Months, 0 = permanent)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.validity_months}
                    onChange={(e) => setFormData({ ...formData, validity_months: Number(e.target.value) })}
                    className="w-full rounded-lg border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-[#2563EB] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg border border-[#CBD5E1] bg-white px-3 py-1.5 text-xs font-semibold text-[#475569] hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingRule}
                  className="rounded-lg bg-[#2563EB] px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-[#1D4ED8] disabled:opacity-50 cursor-pointer"
                >
                  {savingRule ? 'Saving Rule...' : editingRule ? 'Update Rule' : 'Create Rule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
