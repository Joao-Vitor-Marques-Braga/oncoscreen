import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Download,
  Eye,
  MessageSquareShare,
  RefreshCw,
} from "lucide-react";
import { apiClient } from "@/shared/api/client";
import { useAuth } from "@/shared/context/AuthContext";
import {
  Button,
  Card,
  CardHeader,
  MarkdownReportView,
  RiskBadge,
} from "@/shared/components/ui";
import { GradCAMViewer } from "@/features/triage/GradCAMViewer";
import {
  buildClinicalPdfBase64,
  downloadClinicalPdf,
} from "@/shared/utils/generateClinicalPdf";
import type { ExamDetail, ExamListItem } from "@/shared/types/clinical";

export const ExamHistoryPage: React.FC = () => {
  const { user } = useAuth();
  const isDoctor = user?.role === "DOCTOR";
  const [selectedExamId, setSelectedExamId] = useState<string | null>(null);
  const [waMessage, setWaMessage] = useState<string | null>(null);
  const [sendingWa, setSendingWa] = useState(false);

  const {
    data: exams = [],
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["exams"],
    queryFn: async () => (await apiClient.get<ExamListItem[]>("/exams")).data,
  });

  const { data: examDetail, isLoading: loadingDetail } = useQuery({
    queryKey: ["exam-detail", selectedExamId],
    enabled: Boolean(selectedExamId),
    queryFn: async () =>
      (await apiClient.get<ExamDetail>(`/exams/${selectedExamId}`)).data,
  });

  const buildDetailPdfPayload = (detail: ExamDetail) => ({
    examId: detail.id,
    patientName: detail.patient_name,
    patientCpfMasked: detail.patient_cpf_masked,
    patientBirthDate: detail.patient_birth_date,
    patientPhone: detail.patient_phone,
    doctorName: detail.doctor_name,
    finalRisk: detail.guardrail.final_risk,
    anatomicalQuadrant: detail.anatomical_quadrant,
    anamnesis: detail.anamnesis,
    reportText: detail.report_markdown,
    originalImageBase64: detail.original_image_base64,
    gradcamOverlayBase64: detail.gradcam_overlay_base64,
    createdAt: detail.created_at,
  });

  const handleDownloadPdf = async (examId: string) => {
    const detail =
      examDetail && examDetail.id === examId
        ? examDetail
        : (await apiClient.get<ExamDetail>(`/exams/${examId}`)).data;
    downloadClinicalPdf(buildDetailPdfPayload(detail));
  };

  const handleSendWhatsApp = async (examId: string) => {
    setSendingWa(true);
    setWaMessage(null);
    try {
      const detail =
        examDetail && examDetail.id === examId
          ? examDetail
          : (await apiClient.get<ExamDetail>(`/exams/${examId}`)).data;
      const pdfBase64 = buildClinicalPdfBase64(buildDetailPdfPayload(detail));
      const resp = await apiClient.post<{ sent: boolean; message: string }>(
        `/exams/${examId}/whatsapp`,
        { pdf_base64: pdfBase64 }
      );
      setWaMessage(resp.data.message);
      refetch();
    } catch {
      setWaMessage("Falha ao enviar via Evolution API.");
    } finally {
      setSendingWa(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title={isDoctor ? "Histórico Clínico de Triagens" : "Meus Exames e Laudos"}
          subtitle={
            isDoctor
              ? "Consulte exames realizados, baixe laudos em PDF ou envie via WhatsApp."
              : "Acesso exclusivo de leitura aos seus exames e laudos emitidos."
          }
          right={
            <Button type="button" variant="outline" onClick={() => refetch()}>
              <RefreshCw className="w-3.5 h-3.5" />
              Atualizar
            </Button>
          }
        />

        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-6 text-xs text-[#64748B]">Carregando exames...</div>
          ) : exams.length === 0 ? (
            <div className="p-6 text-xs text-[#64748B]">
              Nenhum exame registrado até o momento.
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#F8FAFC] dark:bg-[#1E293B] border-b border-[#CBD5E1] dark:border-[#334155] text-[#475569] dark:text-[#94A3B8]">
                  <th className="py-2.5 px-4 font-semibold">Data</th>
                  <th className="py-2.5 px-4 font-semibold">Paciente</th>
                  <th className="py-2.5 px-4 font-semibold">Localização</th>
                  <th className="py-2.5 px-4 font-semibold">Prob. CNN</th>
                  <th className="py-2.5 px-4 font-semibold">Risco Final</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0] dark:divide-[#334155]">
                {exams.map((ex) => (
                  <tr
                    key={ex.id}
                    className="hover:bg-[#F8FAFC] dark:hover:bg-[#1E293B]/60"
                  >
                    <td className="py-2.5 px-4 font-mono whitespace-nowrap">
                      {new Date(ex.created_at).toLocaleDateString("pt-BR")}
                    </td>
                    <td className="py-2.5 px-4">
                      <div className="font-semibold">{ex.patient_name}</div>
                      <div className="text-[11px] text-[#64748B] font-mono">
                        {ex.patient_cpf_masked}
                      </div>
                    </td>
                    <td className="py-2.5 px-4">{ex.anatomical_quadrant}</td>
                    <td className="py-2.5 px-4 font-mono">
                      {(ex.cnn_probability * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-4">
                      <RiskBadge risk={ex.final_risk} />
                    </td>
                    <td className="py-2.5 px-4 text-right space-x-2 whitespace-nowrap">
                      <Button
                        type="button"
                        variant="outline"
                        className="px-2.5 py-1 text-xs"
                        onClick={() => {
                          setWaMessage(null);
                          setSelectedExamId(ex.id);
                        }}
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Ver Laudo
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        className="px-2.5 py-1 text-xs"
                        onClick={() => handleDownloadPdf(ex.id)}
                      >
                        <Download className="w-3.5 h-3.5" />
                        PDF
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      {selectedExamId && (
        <Card>
          <CardHeader
            title={`Detalhes do Exame #${selectedExamId.slice(0, 8)}`}
            subtitle={
              examDetail
                ? `${examDetail.patient_name} (${examDetail.patient_cpf_masked})`
                : "Carregando..."
            }
            right={examDetail && <RiskBadge risk={examDetail.guardrail.final_risk} />}
          />
          {loadingDetail || !examDetail ? (
            <div className="p-6 text-xs text-[#64748B]">Carregando detalhes do laudo...</div>
          ) : (
            <div className="p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-5 space-y-4">
                {isDoctor ? (
                  <GradCAMViewer
                    originalBase64={examDetail.original_image_base64}
                    heatmapBase64={examDetail.gradcam_heatmap_base64}
                    quadrant={examDetail.anatomical_quadrant}
                  />
                ) : (
                  <div className="space-y-2">
                    <div className="text-xs font-semibold">Imagem Intraoral Analisada</div>
                    <img
                      src={`data:image/jpeg;base64,${examDetail.original_image_base64}`}
                      alt="Imagem analisada"
                      className="w-full rounded border border-[#CBD5E1]"
                    />
                  </div>
                )}

                <div className="p-3 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded-md text-xs space-y-1">
                  <div className="font-semibold">Achados Registrados:</div>
                  <div className="text-[#475569] dark:text-[#94A3B8]">
                    {examDetail.selected_anamnesis_labels.length > 0
                      ? examDetail.selected_anamnesis_labels.join(", ")
                      : "Nenhum fator marcado."}
                  </div>
                </div>
              </div>

              <div className="lg:col-span-7 space-y-4">
                <div className="p-4 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded-md">
                  <MarkdownReportView markdown={examDetail.report_markdown} />
                </div>

                <div className="flex flex-wrap gap-3">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => handleDownloadPdf(examDetail.id)}
                  >
                    <Download className="w-4 h-4" />
                    Baixar Laudo PDF
                  </Button>

                  {isDoctor && (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={sendingWa}
                      onClick={() => handleSendWhatsApp(examDetail.id)}
                    >
                      <MessageSquareShare className="w-4 h-4" />
                      {sendingWa ? "Enviando..." : "Enviar Laudo via WhatsApp"}
                    </Button>
                  )}
                </div>

                {waMessage && (
                  <div className="p-2.5 text-xs bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded">
                    {waMessage}
                  </div>
                )}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

