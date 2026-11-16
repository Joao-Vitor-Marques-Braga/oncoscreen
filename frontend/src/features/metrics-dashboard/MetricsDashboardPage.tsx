import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, ShieldAlert, TrendingUp, Users } from "lucide-react";
import { apiClient } from "@/shared/api/client";
import { Card, CardHeader } from "@/shared/components/ui";
import type { SystemMetrics } from "@/shared/types/clinical";

export const MetricsDashboardPage: React.FC = () => {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: async () => (await apiClient.get<SystemMetrics>("/metrics")).data,
  });

  if (isLoading || !metrics) {
    return <div className="p-6 text-xs text-[#64748B]">Carregando métricas clínicas...</div>;
  }

  const maxRiskCount = Math.max(1, ...Object.values(metrics.risk_distribution));

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-[#475569] dark:text-[#94A3B8]">
            <span>Total de Triagens</span>
            <Activity className="w-4 h-4 text-[#1E3A8A] dark:text-[#60A5FA]" />
          </div>
          <div className="text-2xl font-bold mt-2 font-mono">{metrics.total_exams}</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-[#475569] dark:text-[#94A3B8]">
            <span>Pacientes Cadastrados</span>
            <Users className="w-4 h-4 text-[#1E3A8A] dark:text-[#60A5FA]" />
          </div>
          <div className="text-2xl font-bold mt-2 font-mono">{metrics.total_patients}</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-[#475569] dark:text-[#94A3B8]">
            <span>Ativações de Guardrail</span>
            <ShieldAlert className="w-4 h-4 text-[#B91C1C]" />
          </div>
          <div className="text-2xl font-bold mt-2 font-mono">{metrics.guardrail_activations}</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-[#475569] dark:text-[#94A3B8]">
            <span>ROC-AUC (EfficientNet-B0)</span>
            <TrendingUp className="w-4 h-4 text-[#059669]" />
          </div>
          <div className="text-2xl font-bold mt-2 font-mono">
            {metrics.estimated_roc_auc.toFixed(3)}
          </div>
        </Card>
      </div>

      {/* Clinical Performance & Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader
            title="Distribuição por Estratificação de Risco"
            subtitle="Consolidado após avaliação multimodal e Guardrails de Domínio."
          />
          <div className="p-4 space-y-3">
            {Object.entries(metrics.risk_distribution).map(([label, count]) => {
              const pct = Math.round((count / maxRiskCount) * 100);
              const barColor =
                label === "CRÍTICO" || label === "ALTO"
                  ? "bg-[#B91C1C]"
                  : label === "MODERADO"
                  ? "bg-[#D97706]"
                  : "bg-[#059669]";
              return (
                <div key={label} className="space-y-1 text-xs">
                  <div className="flex justify-between font-medium">
                    <span>{label}</span>
                    <span className="font-mono">{count}</span>
                  </div>
                  <div className="w-full h-2.5 bg-[#E2E8F0] dark:bg-[#1E293B] rounded overflow-hidden">
                    <div className={`h-full ${barColor}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Desempenho Diagnóstico e Concordância"
            subtitle="Indicadores de validação clínica (Sensibilidade vs. Especificidade)."
          />
          <div className="p-4 space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded">
                <div className="text-[#475569] dark:text-[#94A3B8]">Sensibilidade</div>
                <div className="text-lg font-bold font-mono text-[#1E3A8A] dark:text-[#93C5FD]">
                  {(metrics.estimated_sensitivity * 100).toFixed(1)}%
                </div>
              </div>
              <div className="p-3 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded">
                <div className="text-[#475569] dark:text-[#94A3B8]">Especificidade</div>
                <div className="text-lg font-bold font-mono text-[#1E3A8A] dark:text-[#93C5FD]">
                  {(metrics.estimated_specificity * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-[#E2E8F0] dark:border-[#334155]">
              <div className="font-semibold">Concordância Visão vs. Contexto Clínico</div>
              {Object.entries(metrics.concordance_distribution).map(([key, val]) => (
                <div key={key} className="flex justify-between py-1 border-b border-[#F1F5F9] dark:border-[#1E293B]">
                  <span className="font-mono text-[11px]">{key}</span>
                  <span className="font-mono font-bold">{val}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

