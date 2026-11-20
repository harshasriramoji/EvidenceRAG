import React, { useState, useEffect } from 'react';
import { BookOpen, Search, ShieldCheck, ExternalLink, Calendar, Building2, Tag } from 'lucide-react';
import api from '../api/client';

interface GuidelineItem {
  id: number;
  guideline_code: string;
  title: string;
  issuing_authority: string;
  category: string;
  source_url?: string;
  version: string;
  effective_from: string;
  effective_to: string;
  content_preview: string;
  is_approved: boolean;
  is_active: boolean;
}

export const GuidelinesPage: React.FC = () => {
  const [guidelines, setGuidelines] = useState<GuidelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [activeGuideline, setActiveGuideline] = useState<GuidelineItem | null>(null);

  useEffect(() => {
    const fetchGuidelines = async () => {
      try {
        setLoading(true);
        const res = await api.get('/guidelines');
        setGuidelines(res.data);
      } catch (err) {
        console.error('Error fetching guidelines:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchGuidelines();
  }, []);

  const categories = ['All', 'Aadhaar Card', 'Income Certificate', 'Caste Certificate', 'Bonafide Certificate', 'Marks Memo', 'Bank Passbook'];

  const filteredGuidelines = guidelines.filter((g) => {
    const matchesCat = selectedCategory === 'All' || g.category.toLowerCase().includes(selectedCategory.toLowerCase());
    const matchesSearch =
      g.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      g.guideline_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      g.content_preview.toLowerCase().includes(searchTerm.toLowerCase()) ||
      g.issuing_authority.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-6">
      <div className="border-b border-[#CBD5E1] pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Official Regulatory Guidelines</h1>
        <p className="text-sm text-[#475569] mt-1">
          Statutory verification rules and issuing authority standards used by EvidenceRAG's semantic retrieval engine.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-4 rounded-xl border border-[#CBD5E1] shadow-sm">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[#475569] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search guidelines by code, title, authority or keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs border border-[#CBD5E1] rounded-lg focus:outline-none focus:border-[#2563EB]"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                selectedCategory === cat
                  ? 'bg-[#2563EB] text-white'
                  : 'bg-slate-100 text-[#475569] hover:bg-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Guidelines */}
      {loading ? (
        <div className="text-center py-12 text-[#475569] text-sm">Loading regulatory repository...</div>
      ) : filteredGuidelines.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-[#CBD5E1] p-6 text-[#475569] text-sm">
          No guidelines found matching your filter criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredGuidelines.map((g) => (
            <div
              key={g.id}
              className="bg-white border border-[#CBD5E1] rounded-xl p-5 shadow-sm hover:shadow transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="font-mono text-xs font-bold bg-blue-50 text-[#2563EB] px-2 py-0.5 rounded">
                    {g.guideline_code}
                  </span>
                  <div className="flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-medium">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    Approved Standard
                  </div>
                </div>

                <h3 className="text-base font-bold text-[#0F172A] mb-2">{g.title}</h3>

                <p className="text-xs text-[#475569] line-clamp-3 mb-4 leading-relaxed">
                  {g.content_preview}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#475569]">
                <div className="flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                  <span>{g.issuing_authority}</span>
                </div>
                <div className="flex items-center gap-1 font-medium text-slate-600">
                  <Tag className="w-3.5 h-3.5 text-blue-500" />
                  <span>{g.category}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
