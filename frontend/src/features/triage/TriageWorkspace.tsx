import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertTriangle,
  CheckCircle,
  Download,
  FileText,
  ImagePlus,
  MessageSquareShare,
  Play,
  Sliders,
} from "lucide-react";
import { apiClient } from "@/shared/api/client";
import {
  Button,
  Card,
  CardHeader,
  MarkdownReportView,
  RiskBadge,
} from "@/shared/components/ui";
import { PatientLookupCard } from "@/features/patients/PatientLookupCard";
import {
  ANAMNESIS_GROUPS,
  anamnesisSchema,
  type AnamnesisFormValues,
} from "@/features/triage/anamnesisSchema";
import { GradCAMViewer } from "@/features/triage/GradCAMViewer";
import type { PatientSummary, SystemStatus, TriageResult } from "@/shared/types/clinical";

export const TriageWorkspace: React.FC = () => {
  const [selectedPatient, setSelectedPatient] = useState<PatientSummary | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [threshold, setThreshold] = useState<number>(0.5);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [whatsappFeedback, setWhatsappFeedback] = useState<string | null>(null);
  const [sendingWhatsApp, setSendingWhatsApp] = useState(false);

  useEffect(() => {
    apiClient
      .get<SystemStatus>("/settings/status")
      .then((res) => {
        if (typeof res.data.default_threshold === "number") {
          setThreshold(res.data.default_threshold);
        }
      })
      .catch(() => {
        // Keep 0.50 default
      });
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AnamnesisFormValues>({
    resolver: zodResolver(anamnesisSchema),
    defaultValues: anamnesisSchema.parse({}),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = () => setImagePreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const onExecuteTriage = async (anamnesisValues: AnamnesisFormValues) => {
    setErrorMsg(null);
    setWhatsappFeedback(null);
    if (!selectedPatient) {
      setErrorMsg("Selecione ou cadastre um paciente pelo CPF antes de executar a triagem.");
      return;
    }
    if (!imageFile) {
      setErrorMsg("Anexe uma fotografia intraoral da lesão para análise pela CNN.");
      return;
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("patient_id", selectedPatient.id);
      formData.append("threshold", threshold.toFixed(2));
      formData.append("anamnesis_json", JSON.stringify(anamnesisValues));
      formData.append("image", imageFile);

      const resp = await apiClient.post<TriageResult>("/triage/execute", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(resp.data);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Falha ao executar triagem multimodal.";
      setErrorMsg(detail);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!result) return;
    const resp = await apiClient.get(`/exams/${result.exam_id}/pdf`, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([resp.data], { type: "application/pdf" }));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `laudo_oncoscreen_${result.exam_id.slice(0, 8)}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleDispatchWhatsApp = async () => {
    if (!result) return;
    setSendingWhatsApp(true);
    setWhatsappFeedback(null);
    try {
      const resp = await apiClient.post<{ sent: boolean; message: string }>(
        `/exams/${result.exam_id}/whatsapp`
      );
      setWhatsappFeedback(resp.data.message);
    } catch {
      setWhatsappFeedback("Erro ao tentar enviar via WhatsApp.");
    } finally {
      setSendingWhatsApp(false);
    }
  };

  return (
    <div className="space-y-6">
      <PatientLookupCard
        selectedPatient={selectedPatient}
        onSelectPatient={setSelectedPatient}
      />

      <form onSubmit={handleSubmit(onExecuteTriage)} className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Upload + Threshold */}
        <div className="lg:col-span-5 space-y-6">
          <Card>
            <CardHeader
              title="2. Fotografia Intraoral e Sensibilidade"
              subtitle="Imagem analisada pela EfficientNet-B0 com mapa de ativação Grad-CAM."
            />
            <div className="p-4 space-y-4">
              <label className="block border border-dashed border-[#94A3B8] dark:border-[#475569] rounded-md p-4 text-center cursor-pointer hover:bg-[#F8FAFC] dark:hover:bg-[#1E293B] transition-colors">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleFileChange}
                  className="hidden"
                />
                {imagePreview ? (
                  <img
                    src={imagePreview}
                    alt="Pré-visualização intraoral"
                    className="max-h-56 mx-auto rounded border border-[#CBD5E1]"
                  />
                ) : (
                  <div className="py-8 space-y-2 text-[#475569] dark:text-[#94A3B8]">
                    <ImagePlus className="w-8 h-8 mx-auto text-[#1E3A8A] dark:text-[#60A5FA]" />
                    <div className="text-xs font-semibold">
                      Clique para selecionar foto intraoral (.jpg / .png)
                    </div>
                  </div>
                )}
              </label>

              {/* Sensitivity Threshold Slider */}
              <div className="p-3 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded-md space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold flex items-center gap-1.5">
                    <Sliders className="w-3.5 h-3.5 text-[#1E3A8A] dark:text-[#60A5FA]" />
                    Limiar de Sensibilidade (Threshold CNN)
                  </span>
                  <span className="font-mono font-bold text-[#1E3A8A] dark:text-[#93C5FD]">
                    {(threshold * 100).toFixed(0)}%
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
                <div className="flex justify-between text-[10px] text-[#64748B] dark:text-[#94A3B8]">
                  <span>0.10 (Alta Sensibilidade)</span>
                  <span>0.50 (Padrão)</span>
                  <span>0.90 (Alta Especificidade)</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Structured Anamnesis Checkboxes */}
        <div className="lg:col-span-7">
          <Card>
            <CardHeader
              title="3. Anamnese Estruturada (Preenchimento Rápido)"
              subtitle="Marque os fatores de risco, características da lesão e sintomas associados."
            />
            <div className="p-4 space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {ANAMNESIS_GROUPS.map((group) => (
                  <div
                    key={group.title}
                    className="p-3 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded-md space-y-2.5"
                  >
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#1E3A8A] dark:text-[#93C5FD] border-b border-[#CBD5E1] dark:border-[#334155] pb-1.5">
                      {group.title}
                    </h3>
                    <div className="space-y-2">
                      {group.items.map((item) => (
                        <label
                          key={item.key}
                          className="flex items-start gap-2 text-xs cursor-pointer select-none"
                        >
                          <input
                            type="checkbox"
                            {...register(item.key)}
                            className="mt-0.5 rounded border-[#94A3B8] text-[#1E3A8A] focus:ring-[#1E3A8A]"
                          />
                          <span
                            className={
                              item.highlight
                                ? "font-semibold text-[#0F172A] dark:text-white"
                                : "text-[#334155] dark:text-[#CBD5E1]"
                            }
                          >
                            {item.label}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">
                  Observações Clínicas Complementares (opcional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Ex.: Lesão localizada em borda lateral esquerda de língua, indolor à palpação..."
                  {...register("clinical_notes")}
                  className="w-full px-3 py-2 text-xs bg-white dark:bg-[#0F172A] border border-[#CBD5E1] dark:border-[#334155] rounded-md"
                />
                {errors.clinical_notes && (
                  <p className="text-xs text-[#B91C1C] mt-1">{errors.clinical_notes.message}</p>
                )}
              </div>

              {errorMsg && (
                <div className="p-3 text-xs font-medium bg-[#FEF2F2] text-[#991B1B] border border-[#FCA5A5] rounded">
                  {errorMsg}
                </div>
              )}

              <Button type="submit" disabled={submitting} className="w-full py-2.5">
                <Play className="w-4 h-4" />
                {submitting
                  ? "Processando CNN (Grad-CAM) + Guardrails + SLM..."
                  : "Executar Triagem Multimodal"}
              </Button>
            </div>
          </Card>
        </div>
      </form>

      {/* Multimodal Result Panel */}
      {result && (
        <Card>
          <CardHeader
            title="Resultado da Triagem Multimodal & Análise Comparativa"
            subtitle={`Exame #${result.exam_id.slice(0, 8)} • Inferência CPU/GPU: ${result.inference_time_ms.toFixed(0)} ms • Modelo SLM: ${result.model_used}`}
            right={<RiskBadge risk={`Risco Final: ${result.guardrail.final_risk}`} />}
          />
          <div className="p-4 sm:p-6 space-y-6">
            {/* Guardrail Comparative Alert Banner */}
            <div
              className={`p-4 rounded-md border flex items-start gap-3 ${
                result.guardrail.guardrail_triggered
                  ? "bg-[#FEF2F2] dark:bg-[#450A0A] border-[#FCA5A5] dark:border-[#DC2626] text-[#991B1B] dark:text-[#FECACA]"
                  : "bg-[#ECFDF5] dark:bg-[#064E3B] border-[#6EE7B7] dark:border-[#059669] text-[#065F46] dark:text-[#A7F3D0]"
              }`}
            >
              {result.guardrail.guardrail_triggered ? (
                <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
              ) : (
                <CheckCircle className="w-5 h-5 shrink-0 mt-0.5" />
              )}
              <div className="space-y-1 text-xs">
                <div className="font-bold text-sm">{result.guardrail.alert_title}</div>
                <p>{result.guardrail.alert_description}</p>
                <div className="pt-1 flex flex-wrap gap-4 font-mono text-[11px]">
                  <span>Prob. CNN: {(result.cnn_probability * 100).toFixed(1)}%</span>
                  <span>Limiar: {(result.threshold_used * 100).toFixed(0)}%</span>
                  <span>Escore Clínico: {result.guardrail.clinical_score} pts</span>
                  <span>Status: {result.guardrail.concordance_status}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Interactive Grad-CAM */}
              <div className="lg:col-span-5">
                <GradCAMViewer
                  originalBase64={result.original_image_base64}
                  heatmapBase64={result.gradcam_heatmap_base64}
                  quadrant={result.anatomical_quadrant}
                />
              </div>

              {/* SLM Structured Clinical Report */}
              <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
                <div className="p-4 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded-md">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1E3A8A] dark:text-[#93C5FD] mb-3">
                    <FileText className="w-4 h-4" />
                    Laudo Estruturado (SLM)
                  </div>
                  <MarkdownReportView markdown={result.report_markdown} />
                </div>

                <div className="flex flex-wrap gap-3">
                  <Button type="button" variant="secondary" onClick={handleDownloadPDF}>
                    <Download className="w-4 h-4" />
                    Baixar Laudo PDF
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={sendingWhatsApp}
                    onClick={handleDispatchWhatsApp}
                  >
                    <MessageSquareShare className="w-4 h-4" />
                    {sendingWhatsApp ? "Enviando..." : "Enviar Laudo via WhatsApp"}
                  </Button>
                </div>

                {whatsappFeedback && (
                  <div className="p-2.5 text-xs bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded">
                    {whatsappFeedback}
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

