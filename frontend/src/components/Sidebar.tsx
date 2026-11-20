import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Upload,
  FileCheck,
  Files,
  History,
  FileText,
  User,
  ShieldAlert,
  Users,
  Settings,
  Sliders,
  BookOpen,
  Gauge,
  ListChecks,
  Bot,
  Columns2,
  Shield,
  FolderCheck,
  HelpCircle,
  ShieldCheck
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { isAdmin } = useAuth();

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
      isActive
        ? 'bg-blue-50 text-[#2563EB] font-bold border-r-2 border-[#2563EB]'
        : 'text-[#475569] hover:bg-slate-100 hover:text-[#0F172A]'
    }`;

  return (
    <aside className="w-64 shrink-0 border-r border-[#CBD5E1] bg-white min-h-[calc(100vh-4rem)] p-4 flex flex-col justify-between hidden md:flex">
      <div className="space-y-5">
        <div>
          <div className="px-3 text-[11px] font-semibold tracking-wider text-[#475569] uppercase mb-2">
            Verification Workspace
          </div>
          <nav className="space-y-1">
            <NavLink to="/dashboard" className={navClass}>
              <LayoutDashboard className="h-4 w-4" />
              Student Dashboard
            </NavLink>
            <NavLink to="/upload" className={navClass}>
              <Upload className="h-4 w-4" />
              Upload Document
            </NavLink>
            <NavLink to="/verify/single" className={navClass}>
              <FileCheck className="h-4 w-4 text-emerald-600" />
              Mode A: Single Verify
            </NavLink>
            <NavLink to="/verify/cross" className={navClass}>
              <Files className="h-4 w-4 text-[#2563EB]" />
              Mode B: Cross-Verify
            </NavLink>
            <NavLink to="/compare" className={navClass}>
              <Columns2 className="h-4 w-4 text-purple-600" />
              Smart Compare
            </NavLink>
            <NavLink to="/readiness" className={navClass}>
              <Gauge className="h-4 w-4 text-amber-600" />
              Readiness Score
            </NavLink>
            <NavLink to="/checklist" className={navClass}>
              <ListChecks className="h-4 w-4 text-emerald-600" />
              Application Checklist
            </NavLink>
            <NavLink to="/applications" className={navClass}>
              <FolderCheck className="h-4 w-4 text-[#2563EB]" />
              Application Portfolios
            </NavLink>
            <NavLink to="/guidelines" className={navClass}>
              <BookOpen className="h-4 w-4 text-emerald-600" />
              Official Guidelines
            </NavLink>
            <NavLink to="/support" className={navClass}>
              <HelpCircle className="h-4 w-4 text-purple-600" />
              Support & Inquiries
            </NavLink>
            <NavLink to="/assistant" className={navClass}>
              <Bot className="h-4 w-4 text-[#2563EB]" />
              Ask Document AI
            </NavLink>
            <NavLink to="/history" className={navClass}>
              <History className="h-4 w-4" />
              Verification History
            </NavLink>
            <NavLink to="/reports" className={navClass}>
              <FileText className="h-4 w-4" />
              Download Reports
            </NavLink>
          </nav>
        </div>

        {isAdmin && (
          <div>
            <div className="px-3 text-[11px] font-semibold tracking-wider text-amber-600 uppercase mb-2 flex items-center justify-between">
              <span>Admin Administration</span>
              <span className="rounded bg-amber-100 px-1 text-[9px] font-bold text-amber-800">STAFF</span>
            </div>
            <nav className="space-y-1">
              <NavLink to="/admin" end className={navClass}>
                <Sliders className="h-4 w-4 text-amber-600" />
                Admin Dashboard
              </NavLink>
              <NavLink to="/reviewer" className={navClass}>
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                Reviewer Decision Portal
              </NavLink>
              <NavLink to="/admin/reviews" className={navClass}>
                <ShieldAlert className="h-4 w-4 text-rose-600" />
                Review Flagged Issues
              </NavLink>
              <NavLink to="/admin/audit-logs" className={navClass}>
                <Shield className="h-4 w-4 text-purple-600" />
                Audit Trail
              </NavLink>
              <NavLink to="/admin/rules" className={navClass}>
                <Settings className="h-4 w-4" />
                Verification Rules
              </NavLink>
              <NavLink to="/admin/knowledge-base" className={navClass}>
                <BookOpen className="h-4 w-4 text-purple-600" />
                RAG Knowledge Base
              </NavLink>
              <NavLink to="/admin/users" className={navClass}>
                <Users className="h-4 w-4" />
                Registered Users
              </NavLink>
            </nav>
          </div>
        )}
      </div>

      <div className="border-t border-slate-100 pt-4">
        <NavLink to="/profile" className={navClass}>
          <User className="h-4 w-4" />
          My Profile & Settings
        </NavLink>
        <div className="mt-3 rounded-lg bg-[#F8FAFF] p-2.5 text-[11px] text-[#475569] border border-slate-100">
          <div className="font-semibold text-[#0F172A]">EvidenceRAG 2.0</div>
          <div>Pre-submission Scholarship Verification with Grounded RAG</div>
        </div>
      </div>
    </aside>
  );
};
