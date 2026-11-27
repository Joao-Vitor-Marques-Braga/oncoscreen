import { jsPDF } from "jspdf";
import type { AnamnesisData } from "@/shared/types/clinical";

export interface ClinicalPdfPayload {
  examId: string;
  patientName: string;
  patientCpfMasked: string;
  patientBirthDate: string;
  patientPhone: string;
  doctorName: string;
  finalRisk: string;
  anatomicalQuadrant: string;
  anamnesis: AnamnesisData;
  reportText: string;
  originalImageBase64?: string;
  gradcamOverlayBase64?: string;
  createdAt: string;
}

/**
 * Cleans raw SLM output: strips ```markdown fences, ### hashes, bold **, backticks,
 * and orphaned bullet lines so text looks like a clean medical report.
 */
export function sanitizeClinicalText(raw: string): string {
  let text = (raw || "").trim();

  // Strip wrapping code fences like ```markdown ... ```
  text = text.replace(/^```[a-zA-Z0-9_-]*\s*\n?/gm, "");
  text = text.replace(/\n?```\s*$/gm, "");
  text = text.replace(/```[a-zA-Z0-9_-]*/g, "");

  // Collapse orphaned bullets ("•\nItem" -> "- Item")
  text = text.replace(/^\s*[•●▪]\s*\n+\s*/gm, "- ");
  text = text.replace(/^\s*[•●▪*]\s+/gm, "- ");

  const lines = text.split("\n").map((line) => {
    let s = line.trim();
    if (!s) return "";
    s = s.replace(/`/g, "").replace(/\*\*/g, "");
    if (/^#{1,6}\s+/.test(s)) {
      s = s.replace(/^#{1,6}\s+/, "").trim();
    }
    return s;
  });

  return lines
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function formatBirthDateBR(isoDate: string): string {
  if (!isoDate) return "-";
  const parts = isoDate.slice(0, 10).split("-");
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  return isoDate;
}

function formatDateTimeBR(isoDateTime: string): string {
  const dt = new Date(isoDateTime);
  if (Number.isNaN(dt.getTime())) return isoDateTime;
  return dt.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function createClinicalPdfDoc(data: ClinicalPdfPayload): jsPDF {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth(); // 210
  const pageH = doc.internal.pageSize.getHeight(); // 297
  const marginX = 18;
  const contentW = pageW - marginX * 2; // 174
  const bottomLimit = pageH - 26; // Reserve space for fixed footer

  const NAVY: [number, number, number] = [30, 58, 138];
  const ACCENT_BLUE: [number, number, number] = [219, 234, 254];
  const SLATE: [number, number, number] = [15, 23, 42];
  const MUTED: [number, number, number] = [71, 85, 105];
  const BORDER: [number, number, number] = [203, 213, 225];
  const BG_LIGHT: [number, number, number] = [248, 250, 252];

  let y = 16;

  const ensureSpace = (neededMm: number) => {
    if (y + neededMm > bottomLimit) {
      doc.addPage();
      y = 18;
    }
  };

  // 1. Clean Medical Letterhead (Vector Cross Emblem + Clinic Name)
  doc.setFillColor(...ACCENT_BLUE);
  doc.setDrawColor(...NAVY);
  doc.setLineWidth(0.35);
  doc.circle(marginX + 6, y + 6, 6, "FD");
  doc.setFillColor(...NAVY);
  doc.rect(marginX + 4.8, y + 2.5, 2.4, 7, "F");
  doc.rect(marginX + 2.5, y + 4.8, 7, 2.4, "F");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.setTextColor(...NAVY);
  doc.text("OncoScreen Saúde — Estomatologia e Triagem Oral", marginX + 16, y + 5.5);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(...MUTED);
  doc.text("Relatório de Avaliação Clínica", marginX + 16, y + 10.5);

  y += 15;
  doc.setDrawColor(...NAVY);
  doc.setLineWidth(0.5);
  doc.line(marginX, y, pageW - marginX, y);
  y += 5;

  // 2. Patient & Attendance Identification Table (auto-wrapped cells, zero overlap)
  const infoRows: [string, string, string, string][] = [
    ["Paciente:", data.patientName, "CPF:", data.patientCpfMasked],
    ["Data de Nasc.:", formatBirthDateBR(data.patientBirthDate), "Telefone:", data.patientPhone || "-"],
    ["Médico Resp.:", data.doctorName || "Médico Responsável", "Data do Exame:", formatDateTimeBR(data.createdAt)],
    ["Classificação:", data.finalRisk, "Região Avaliada:", data.anatomicalQuadrant],
  ];

  const colW = [26, 61, 28, 59]; // Total = 174mm
  doc.setFontSize(8.5);
  for (let rIdx = 0; rIdx < infoRows.length; rIdx++) {
    const [l1, v1, l2, v2] = infoRows[rIdx];
    const v1Lines = doc.splitTextToSize(v1, colW[1] - 4);
    const v2Lines = doc.splitTextToSize(v2, colW[3] - 4);
    const maxLines = Math.max(v1Lines.length, v2Lines.length, 1);
    const rowH = maxLines * 4.2 + 3.2;

    ensureSpace(rowH);

    doc.setFillColor(...BG_LIGHT);
    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.2);

    let cx = marginX;
    for (let c = 0; c < 4; c++) {
      doc.rect(cx, y, colW[c], rowH, "FD");
      cx += colW[c];
    }

    const textY = y + 4.4;
    doc.setTextColor(...SLATE);

    doc.setFont("helvetica", "bold");
    doc.text(l1, marginX + 2, textY);

    doc.setFont("helvetica", rIdx === 3 ? "bold" : "normal");
    doc.text(v1Lines, marginX + colW[0] + 2, textY);

    doc.setFont("helvetica", "bold");
    doc.text(l2, marginX + colW[0] + colW[1] + 2, textY);

    doc.setFont("helvetica", "normal");
    doc.text(v2Lines, marginX + colW[0] + colW[1] + colW[2] + 2, textY);

    y += rowH;
  }

  y += 6;

  // 3. Structured Medical History Table with Checkboxes ([X] / [ ])
  ensureSpace(14);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10.5);
  doc.setTextColor(...NAVY);
  doc.text("Histórico Clínico e Achados da Anamnese", marginX, y);
  y += 3.5;

  const a = data.anamnesis;
  const checklist: [boolean, string][] = [
    [a.active_smoking, "Tabagismo ativo"],
    [a.former_smoker, "Ex-tabagista"],
    [a.frequent_alcohol, "Etilismo frequente"],
    [a.chronic_sun_exposure, "Exposição solar crônica (lábio)"],
    [a.family_cancer_history, "Histórico familiar de câncer"],
    [a.evolution_gt_14_days, "Evolução > 14 dias"],
    [a.non_healing_ulcer, "Úlcera que não cicatriza"],
    [a.leukoplakia, "Mancha branca (Leucoplasia)"],
    [a.erythroplakia, "Mancha vermelha (Eritroplasia)"],
    [a.induration_raised_borders, "Endurecimento / Bordas elevadas"],
    [a.spontaneous_or_touch_bleeding, "Sangramento espontâneo/toque"],
    [a.local_pain, "Dor local"],
    [a.odynophagia, "Odinofagia (dor ao engolir)"],
    [a.dysphagia, "Disfagia"],
    [a.cervical_lymphadenopathy, "Linfonodomegalia cervical"],
    [a.recent_weight_loss, "Perda de peso recente"],
  ];

  const half = checklist.length / 2;
  const chkW = 10;
  const lblW = (contentW - chkW * 2) / 2; // 77mm each
  const chkRowH = 6.2;

  doc.setFontSize(8.3);
  for (let i = 0; i < half; i++) {
    ensureSpace(chkRowH);
    const [lFlag, lLabel] = checklist[i];
    const [rFlag, rLabel] = checklist[i + half];

    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.2);

    // Left checkbox cell
    doc.setFillColor(...ACCENT_BLUE);
    doc.rect(marginX, y, chkW, chkRowH, "FD");
    // Left label cell
    doc.setFillColor(255, 255, 255);
    doc.rect(marginX + chkW, y, lblW, chkRowH, "FD");
    // Right checkbox cell
    doc.setFillColor(...ACCENT_BLUE);
    doc.rect(marginX + chkW + lblW, y, chkW, chkRowH, "FD");
    // Right label cell
    doc.setFillColor(255, 255, 255);
    doc.rect(marginX + chkW * 2 + lblW, y, lblW, chkRowH, "FD");

    doc.setTextColor(...SLATE);
    doc.setFont("helvetica", lFlag ? "bold" : "normal");
    doc.text(lFlag ? "[X]" : "[ ]", marginX + chkW / 2, y + 4.2, { align: "center" });
    doc.text(lLabel, marginX + chkW + 2.5, y + 4.2);

    doc.setFont("helvetica", rFlag ? "bold" : "normal");
    doc.text(rFlag ? "[X]" : "[ ]", marginX + chkW + lblW + chkW / 2, y + 4.2, { align: "center" });
    doc.text(rLabel, marginX + chkW * 2 + lblW + 2.5, y + 4.2);

    y += chkRowH;
  }

  if (a.clinical_notes?.trim()) {
    y += 4;
    const noteLines = doc.splitTextToSize(`Observações Clínicas: ${a.clinical_notes.trim()}`, contentW);
    ensureSpace(noteLines.length * 4.5 + 2);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.8);
    doc.setTextColor(...SLATE);
    doc.text(noteLines, marginX, y);
    y += noteLines.length * 4.3;
  }

  // 4. Side-by-side Clinical Images
  if (data.originalImageBase64 && data.gradcamOverlayBase64) {
    y += 6;
    const imgBoxH = 56;
    ensureSpace(imgBoxH + 14);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(10.5);
    doc.setTextColor(...NAVY);
    doc.text("Registro Fotográfico e Mapeamento da Lesão", marginX, y);
    y += 3.5;

    const halfW = contentW / 2;
    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.25);
    doc.rect(marginX, y, halfW, imgBoxH);
    doc.rect(marginX + halfW, y, halfW, imgBoxH);

    const imgW = 72;
    const imgH = 46;
    const padX = (halfW - imgW) / 2;
    try {
      doc.addImage(
        `data:image/jpeg;base64,${data.originalImageBase64}`,
        "JPEG",
        marginX + padX,
        y + 2.5,
        imgW,
        imgH
      );
      doc.addImage(
        `data:image/jpeg;base64,${data.gradcamOverlayBase64}`,
        "JPEG",
        marginX + halfW + padX,
        y + 2.5,
        imgW,
        imgH
      );
    } catch {
      // Ignore malformed base64 image in unit tests
    }

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...MUTED);
    doc.text("Fotografia Intraoral", marginX + halfW / 2, y + imgBoxH - 2.5, { align: "center" });
    doc.text(
      `Mapeamento de Região (${data.anatomicalQuadrant})`,
      marginX + halfW + halfW / 2,
      y + imgBoxH - 2.5,
      { align: "center" }
    );

    y += imgBoxH + 4;
  }

  // 5. Clinical Report Body (sanitized, zero markdown artifacts)
  y += 4;
  ensureSpace(12);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10.5);
  doc.setTextColor(...NAVY);
  doc.text("Parecer Clínico e Conduta Recomendada", marginX, y);
  y += 5;

  const cleanBody = sanitizeClinicalText(data.reportText);
  const bodyLines = cleanBody.split("\n");

  for (const rawLine of bodyLines) {
    const line = rawLine.trim();
    if (!line) {
      y += 2;
      continue;
    }

    const isSectionHeading = /^\d+\.\s+/.test(line);
    const isBullet = line.startsWith("- ");

    if (isSectionHeading) {
      ensureSpace(9);
      y += 2;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(9.8);
      doc.setTextColor(...NAVY);
      doc.text(line, marginX, y);
      y += 4.8;
    } else if (isBullet) {
      const bulletText = line.slice(2).trim();
      const wrapped = doc.splitTextToSize(bulletText, contentW - 5);
      ensureSpace(wrapped.length * 4.4 + 2);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      doc.setTextColor(...SLATE);
      doc.text("•", marginX + 1.5, y);
      doc.text(wrapped, marginX + 5, y);
      y += wrapped.length * 4.3 + 1;
    } else {
      const wrapped = doc.splitTextToSize(line, contentW);
      ensureSpace(wrapped.length * 4.4 + 2);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      doc.setTextColor(...SLATE);
      doc.text(wrapped, marginX, y);
      y += wrapped.length * 4.3 + 1.2;
    }
  }

  // 6. Centered Signature Block positioned lower on the final page
  ensureSpace(34);
  // Push signature nicely down towards bottom if there's plenty of empty vertical space
  const targetSigY = Math.max(y + 18, bottomLimit - 24);
  y = Math.min(targetSigY, bottomLimit - 16);

  doc.setDrawColor(...SLATE);
  doc.setLineWidth(0.3);
  doc.line(pageW / 2 - 42, y, pageW / 2 + 42, y);

  doc.setFont("helvetica", "bold");
  doc.setFontSize(9.5);
  doc.setTextColor(...SLATE);
  doc.text(data.doctorName || "Médico Responsável", pageW / 2, y + 5, { align: "center" });

  doc.setFont("helvetica", "normal");
  doc.setFontSize(8.2);
  doc.setTextColor(...MUTED);
  doc.text("Médico Responsável — Assinatura / Carimbo", pageW / 2, y + 9.5, { align: "center" });

  // 7. Fixed Institutional Footer on EVERY page
  const totalPages = doc.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    const lineY = pageH - 17;
    const textY = pageH - 12;

    doc.setDrawColor(...NAVY);
    doc.setLineWidth(0.35);
    doc.line(marginX, lineY, pageW - marginX, lineY);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...MUTED);
    doc.text("contato@oncoscreen.ai", marginX, textY);
    doc.text("Serviço de Estomatologia e Triagem Clínica", pageW / 2, textY, { align: "center" });
    doc.text("Documento de Apoio Clínico", pageW - marginX, textY, { align: "right" });
  }

  return doc;
}

export function downloadClinicalPdf(data: ClinicalPdfPayload): void {
  const doc = createClinicalPdfDoc(data);
  doc.save(`laudo_oncoscreen_${data.examId.slice(0, 8)}.pdf`);
}
