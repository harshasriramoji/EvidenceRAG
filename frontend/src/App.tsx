import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

// Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { StudentDashboard } from './pages/StudentDashboard';
import { DocumentUploadPage } from './pages/DocumentUploadPage';
import { SingleVerifyPage } from './pages/SingleVerifyPage';
import { MultiVerifyPage } from './pages/MultiVerifyPage';
import { DocumentDetailsPage } from './pages/DocumentDetailsPage';
import { EvidenceViewerPage } from './pages/EvidenceViewerPage';
import { SmartComparePage } from './pages/SmartComparePage';
import { ReadinessPage } from './pages/ReadinessPage';
import { ChecklistPage } from './pages/ChecklistPage';
import { AssistantPage } from './pages/AssistantPage';
import { HistoryPage } from './pages/HistoryPage';
import { VersionHistoryPage } from './pages/VersionHistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { ProfilePage } from './pages/ProfilePage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { GuidelinesPage } from './pages/GuidelinesPage';
import { SupportPage } from './pages/SupportPage';

// Admin Pages
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AdminReviewPage } from './pages/admin/AdminReviewPage';
import { AdminAuditPage } from './pages/admin/AdminAuditPage';
import { AdminRulesPage } from './pages/admin/AdminRulesPage';
import { AdminUsersPage } from './pages/admin/AdminUsersPage';
import { AdminKnowledgePage } from './pages/admin/AdminKnowledgePage';
import { ReviewerPortalPage } from './pages/admin/ReviewerPortalPage';

const ProtectedLayout: React.FC<{ children: React.ReactNode; adminOnly?: boolean }> = ({
  children,
  adminOnly = false,
}) => {
  const { user, isLoading, isAdmin } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#F8FAFF] text-xs text-[#475569]">
        Authenticating session...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-[#F8FAFF] flex flex-col text-[#0F172A]">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication & Welcome Pages */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Student & Shared Workspaces */}
          <Route
            path="/dashboard"
            element={
              <ProtectedLayout>
                <StudentDashboard />
              </ProtectedLayout>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedLayout>
                <DocumentUploadPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/verify/single"
            element={
              <ProtectedLayout>
                <SingleVerifyPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/verify-single"
            element={
              <ProtectedLayout>
                <SingleVerifyPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/verify/cross"
            element={
              <ProtectedLayout>
                <MultiVerifyPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/verify-cross"
            element={
              <ProtectedLayout>
                <MultiVerifyPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/documents/:id"
            element={
              <ProtectedLayout>
                <DocumentDetailsPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/evidence/:issueId"
            element={
              <ProtectedLayout>
                <EvidenceViewerPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/compare"
            element={
              <ProtectedLayout>
                <SmartComparePage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/readiness"
            element={
              <ProtectedLayout>
                <ReadinessPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/checklist"
            element={
              <ProtectedLayout>
                <ChecklistPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/assistant"
            element={
              <ProtectedLayout>
                <AssistantPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedLayout>
                <HistoryPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/documents/:id/versions"
            element={
              <ProtectedLayout>
                <VersionHistoryPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedLayout>
                <ReportsPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedLayout>
                <ProfilePage />
              </ProtectedLayout>
            }
          />

          {/* Admin Protected Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedLayout adminOnly>
                <AdminDashboard />
              </ProtectedLayout>
            }
          />
          <Route
            path="/admin/reviews"
            element={
              <ProtectedLayout adminOnly>
                <AdminReviewPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/admin/audit-logs"
            element={
              <ProtectedLayout adminOnly>
                <AdminAuditPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/admin/rules"
            element={
              <ProtectedLayout adminOnly>
                <AdminRulesPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/admin/knowledge-base"
            element={
              <ProtectedLayout adminOnly>
                <AdminKnowledgePage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedLayout adminOnly>
                <AdminUsersPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/applications"
            element={
              <ProtectedLayout>
                <ApplicationsPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/guidelines"
            element={
              <ProtectedLayout>
                <GuidelinesPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/support"
            element={
              <ProtectedLayout>
                <SupportPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/reviewer"
            element={
              <ProtectedLayout adminOnly>
                <ReviewerPortalPage />
              </ProtectedLayout>
            }
          />

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
