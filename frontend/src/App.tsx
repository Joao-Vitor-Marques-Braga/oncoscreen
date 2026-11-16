import React, { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "@/shared/context/AuthContext";
import { ThemeProvider } from "@/shared/context/ThemeContext";
import { ClinicalLayout, type NavTab } from "@/shared/components/ClinicalLayout";
import { LoginPage } from "@/features/auth/LoginPage";
import { TriageWorkspace } from "@/features/triage/TriageWorkspace";
import { ExamHistoryPage } from "@/features/exam-history/ExamHistoryPage";
import { MetricsDashboardPage } from "@/features/metrics-dashboard/MetricsDashboardPage";
import { ModelSettingsPage } from "@/features/model-settings/ModelSettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const AuthenticatedShell: React.FC = () => {
  const { user } = useAuth();
  const isDoctor = user?.role === "DOCTOR";
  const [activeTab, setActiveTab] = useState<NavTab>(isDoctor ? "triage" : "history");

  useEffect(() => {
    if (!user) return;
    setActiveTab(user.role === "DOCTOR" ? "triage" : "history");
  }, [user?.role]);

  if (!user) {
    return <LoginPage />;
  }

  return (
    <ClinicalLayout activeTab={activeTab} onTabChange={setActiveTab}>
      {isDoctor && activeTab === "triage" && <TriageWorkspace />}
      {activeTab === "history" && <ExamHistoryPage />}
      {isDoctor && activeTab === "metrics" && <MetricsDashboardPage />}
      {isDoctor && activeTab === "settings" && <ModelSettingsPage />}
    </ClinicalLayout>
  );
};

export const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <AuthProvider>
        <AuthenticatedShell />
      </AuthProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;

