import React from "react";
import {
  Activity,
  BarChart3,
  ClipboardList,
  LogOut,
  Microscope,
  Moon,
  Settings,
  Sun,
  UserCheck,
} from "lucide-react";
import { useAuth } from "@/shared/context/AuthContext";
import { useTheme } from "@/shared/context/ThemeContext";

export type NavTab = "triage" | "history" | "metrics" | "settings";

interface ClinicalLayoutProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  children: React.ReactNode;
}

export const ClinicalLayout: React.FC<ClinicalLayoutProps> = ({
  activeTab,
  onTabChange,
  children,
}) => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const isDoctor = user?.role === "DOCTOR";

  const navItems: { id: NavTab; label: string; icon: React.ReactNode; doctorOnly?: boolean }[] = [
    {
      id: "triage",
      label: "Triagem Multimodal",
      icon: <Microscope className="w-4 h-4" />,
      doctorOnly: true,
    },
    {
      id: "history",
      label: isDoctor ? "Histórico de Exames" : "Meus Exames",
      icon: <ClipboardList className="w-4 h-4" />,
    },
    {
      id: "metrics",
      label: "Métricas Clínicas",
      icon: <BarChart3 className="w-4 h-4" />,
      doctorOnly: true,
    },
    {
      id: "settings",
      label: "Configurações & Modelos",
      icon: <Settings className="w-4 h-4" />,
      doctorOnly: true,
    },
  ];

  const visibleNav = navItems.filter((item) => !item.doctorOnly || isDoctor);

  return (
    <div className="min-h-screen flex flex-col bg-[#F8FAFC] dark:bg-[#0B1120] text-[#0F172A] dark:text-[#F8FAFC]">
      {/* PubMed / Institutional Top Bar */}
      <header className="bg-[#1E3A8A] text-white border-b border-[#172554]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-white text-[#1E3A8A] p-1.5 rounded">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-base tracking-tight leading-none">
                OncoScreen.AI
              </div>
              <div className="text-[11px] text-[#CBD5E1] leading-tight">
                OralCare-Vision CDSS • Triagem HNSCC
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs bg-[#172554] px-3 py-1.5 rounded border border-[#3B82F6]/30">
              <UserCheck className="w-3.5 h-3.5 text-[#93C5FD]" />
              <span className="font-medium">{user?.full_name}</span>
              <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-white text-[#1E3A8A]">
                {isDoctor ? "MÉDICO" : "PACIENTE"}
              </span>
            </div>

            <button
              type="button"
              onClick={toggleTheme}
              aria-label="Alternar tema claro/escuro"
              className="p-2 rounded border border-white/20 hover:bg-[#172554] transition-colors"
              title={isDark ? "Modo Claro Clínico" : "Modo Escuro Clínico"}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button
              type="button"
              onClick={logout}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border border-white/25 hover:bg-[#172554] transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sair</span>
            </button>
          </div>
        </div>

        {/* Navigation Strip */}
        <nav className="bg-white dark:bg-[#111827] border-b border-[#CBD5E1] dark:border-[#334155]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 flex overflow-x-auto gap-1">
            {visibleNav.map((item) => {
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onTabChange(item.id)}
                  className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                    active
                      ? "border-[#1E3A8A] text-[#1E3A8A] dark:border-[#60A5FA] dark:text-[#60A5FA] bg-[#F8FAFC] dark:bg-[#1E293B]"
                      : "border-transparent text-[#475569] dark:text-[#94A3B8] hover:text-[#0F172A] dark:hover:text-white"
                  }`}
                >
                  {item.icon}
                  {item.label}
                </button>
              );
            })}
          </div>
        </nav>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>

      <footer className="border-t border-[#CBD5E1] dark:border-[#334155] bg-white dark:bg-[#111827] py-3 px-4 text-center text-xs text-[#64748B] dark:text-[#94A3B8]">
        OncoScreen.AI (OralCare-Vision CDSS) • Sistema de Apoio à Decisão Clínica — Uso exclusivo para triagem precoce.
      </footer>
    </div>
  );
};

