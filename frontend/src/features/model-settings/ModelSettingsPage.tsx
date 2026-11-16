import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Cpu, MessageCircle, RefreshCw, Save, Sparkles } from "lucide-react";
import { apiClient } from "@/shared/api/client";
import { Button, Card, CardHeader } from "@/shared/components/ui";
import type { SystemStatus } from "@/shared/types/clinical";

export const ModelSettingsPage: React.FC = () => {
  const { data: status, isLoading, refetch } = useQuery({
    queryKey: ["system-status"],
    queryFn: async () => (await apiClient.get<SystemStatus>("/settings/status")).data,
  });

  const [threshold, setThreshold] = useState<number>(0.5);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  useEffect(() => {
    if (status?.default_threshold !== undefined) {
      setThreshold(status.default_threshold);
    }
  }, [status]);

  const handleSaveThreshold = async () => {
    setSavedMsg(null);
    await apiClient.put("/settings/threshold", { default_threshold: threshold });
    setSavedMsg("Limiar padrão atualizado com sucesso.");
    refetch();
  };

  if (isLoading || !status) {
    return <div className="p-6 text-xs text-[#64748B]">Verificando status dos motores...</div>;
  }

  const ollamaOnline = Boolean(status.ollama?.online);
  const waOnline = Boolean(status.whatsapp?.online);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title="Calibração Padrão do Modelo de Visão"
          subtitle="Define o threshold inicial utilizado na tela de triagem multimodal."
          right={
            <Button type="button" variant="outline" onClick={() => refetch()}>
              <RefreshCw className="w-3.5 h-3.5" />
              Verificar Status
            </Button>
          }
        />
        <div className="p-4 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex-1 space-y-1">
              <div className="flex justify-between text-xs font-semibold">
                <span>Threshold Padrão (EfficientNet-B0)</span>
                <span className="font-mono text-[#1E3A8A] dark:text-[#93C5FD]">
                  {threshold.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={0.1}
                max={0.9}
                step={0.05}
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full accent-[#1E3A8A]"
              />
            </div>
            <Button type="button" onClick={handleSaveThreshold}>
              <Save className="w-4 h-4" />
              Salvar Limiar
            </Button>
          </div>
          {savedMsg && (
            <div className="p-2 text-xs bg-[#ECFDF5] text-[#065F46] border border-[#6EE7B7] rounded">
              {savedMsg}
            </div>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-[#1E3A8A] dark:text-[#93C5FD]">
            <Cpu className="w-4 h-4" />
            PyTorch Vision Engine
          </div>
          <div className="text-xs space-y-1 font-mono">
            <div>Dispositivo: {String(status.vision.device)}</div>
            <div>Threads CPU: {String(status.vision.cpu_threads ?? "GPU")}</div>
            <div>Pesos (.pth): {status.vision.weights_loaded ? "Carregados" : "Inicializado"}</div>
          </div>
        </Card>

        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-[#1E3A8A] dark:text-[#93C5FD]">
            <span className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              Ollama Local SLM
            </span>
            <span
              className={`px-2 py-0.5 rounded text-[10px] ${
                ollamaOnline ? "bg-[#ECFDF5] text-[#065F46]" : "bg-[#FFFBEB] text-[#92400E]"
              }`}
            >
              {ollamaOnline ? "ONLINE" : "FALLBACK"}
            </span>
          </div>
          <div className="text-xs space-y-1 font-mono">
            <div>Modelo: {String(status.ollama.configured_model)}</div>
            <div>URL: {String(status.ollama.base_url)}</div>
          </div>
        </Card>

        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-[#1E3A8A] dark:text-[#93C5FD]">
            <span className="flex items-center gap-2">
              <MessageCircle className="w-4 h-4" />
              Evolution API (WhatsApp)
            </span>
            <span
              className={`px-2 py-0.5 rounded text-[10px] ${
                waOnline ? "bg-[#ECFDF5] text-[#065F46]" : "bg-[#FFFBEB] text-[#92400E]"
              }`}
            >
              {waOnline ? "CONECTADA" : "OFFLINE"}
            </span>
          </div>
          <div className="text-xs space-y-1 font-mono">
            <div>Instância: {String(status.whatsapp.instance)}</div>
            <div>Configurada: {status.whatsapp.configured ? "Sim" : "Não (.env)"}</div>
          </div>
        </Card>
      </div>
    </div>
  );
};

