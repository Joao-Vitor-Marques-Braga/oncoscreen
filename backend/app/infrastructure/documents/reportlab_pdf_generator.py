"""Formal clinical PDF report generator styled as a medical clinic report."""

from __future__ import annotations

import io
import re
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Circle, Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.domain.entities.exam import Exam
from app.domain.entities.patient import Patient
from app.domain.interfaces.documents import PDFGenerator


class ReportLabPDFGenerator(PDFGenerator):
    """Generates clean, hospital-style medical reports without AI-jargon aesthetics."""

    NAVY = colors.HexColor("#1E3A8A")
    ACCENT_BLUE = colors.HexColor("#BFDBFE")
    SLATE = colors.HexColor("#0F172A")
    MUTED = colors.HexColor("#475569")
    BORDER = colors.HexColor("#CBD5E1")
    BG_LIGHT = colors.HexColor("#F8FAFC")

    def generate_exam_pdf(
        self,
        exam: Exam,
        patient: Patient,
        doctor_name: str,
        original_image_bytes: bytes,
        gradcam_overlay_bytes: bytes,
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=1.8 * cm,
            rightMargin=1.8 * cm,
            topMargin=1.4 * cm,
            bottomMargin=2.4 * cm,
            title=f"Relatório Médico - {patient.full_name}",
        )

        styles = getSampleStyleSheet()
        clinic_title_style = ParagraphStyle(
            "ClinicTitle",
            parent=styles["Heading1"],
            fontSize=15,
            leading=18,
            textColor=self.NAVY,
            spaceAfter=1,
        )
        clinic_sub_style = ParagraphStyle(
            "ClinicSub",
            parent=styles["Normal"],
            fontSize=9,
            textColor=self.MUTED,
        )
        section_style = ParagraphStyle(
            "MedicalSection",
            parent=styles["Heading2"],
            fontSize=10.5,
            textColor=self.NAVY,
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "MedicalBody",
            parent=styles["Normal"],
            fontSize=9.2,
            leading=13.5,
            textColor=self.SLATE,
        )
        cell_style = ParagraphStyle(
            "CellText",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=self.SLATE,
        )
        cell_bold_style = ParagraphStyle(
            "CellBold",
            parent=cell_style,
            fontName="Helvetica-Bold",
        )

        elements: list = []

        # 1. Clean Medical Letterhead (icon + clinic name)
        emblem = self._build_medical_emblem()
        header_table = Table(
            [
                [
                    emblem,
                    [
                        Paragraph("<b>OncoScreen Saúde</b> — Estomatologia e Triagem Oral", clinic_title_style),
                        Paragraph("Relatório de Avaliação Clínica", clinic_sub_style),
                    ],
                ]
            ],
            colWidths=[1.6 * cm, 15.8 * cm],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, -1), 1.2, self.NAVY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # 2. Patient & Consultation Identification (using Paragraphs to prevent overlap)
        g = exam.guardrail_assessment
        info_data = [
            [
                Paragraph("Paciente:", cell_bold_style),
                Paragraph(escape(patient.full_name), cell_style),
                Paragraph("CPF:", cell_bold_style),
                Paragraph(patient.cpf.masked, cell_style),
            ],
            [
                Paragraph("Data de Nasc.:", cell_bold_style),
                Paragraph(patient.birth_date.strftime("%d/%m/%Y"), cell_style),
                Paragraph("Telefone:", cell_bold_style),
                Paragraph(escape(patient.phone_whatsapp), cell_style),
            ],
            [
                Paragraph("Médico Resp.:", cell_bold_style),
                Paragraph(escape(doctor_name), cell_style),
                Paragraph("Data do Exame:", cell_bold_style),
                Paragraph(exam.created_at.strftime("%d/%m/%Y %H:%M"), cell_style),
            ],
            [
                Paragraph("Classificação:", cell_bold_style),
                Paragraph(f"<b>{escape(g.final_risk.value)}</b>", cell_style),
                Paragraph("Região Avaliada:", cell_bold_style),
                Paragraph(escape(exam.anatomical_quadrant.value), cell_style),
            ],
        ]
        info_table = Table(info_data, colWidths=[2.8 * cm, 6.2 * cm, 3.0 * cm, 5.4 * cm])
        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.BG_LIGHT),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(info_table)
        elements.append(Spacer(1, 6))

        # 3. Structured Medical History Table with Checkboxes (2-column clinical form)
        elements.append(Paragraph("Histórico Clínico e Achados da Anamnese", section_style))
        a = exam.anamnesis
        checklist_items = [
            (a.active_smoking, "Tabagismo ativo"),
            (a.former_smoker, "Ex-tabagista"),
            (a.frequent_alcohol, "Etilismo frequente"),
            (a.chronic_sun_exposure, "Exposição solar crônica (lábio)"),
            (a.family_cancer_history, "Histórico familiar de câncer"),
            (a.evolution_gt_14_days, "Evolução > 14 dias"),
            (a.non_healing_ulcer, "Úlcera que não cicatriza"),
            (a.leukoplakia, "Mancha branca (Leucoplasia)"),
            (a.erythroplakia, "Mancha vermelha (Eritroplasia)"),
            (a.induration_raised_borders, "Endurecimento / Bordas elevadas"),
            (a.spontaneous_or_touch_bleeding, "Sangramento espontâneo/toque"),
            (a.local_pain, "Dor local"),
            (a.odynophagia, "Odinofagia (dor ao engolir)"),
            (a.dysphagia, "Disfagia"),
            (a.cervical_lymphadenopathy, "Linfonodomegalia cervical"),
            (a.recent_weight_loss, "Perda de peso recente"),
        ]

        half = len(checklist_items) // 2
        left_col = checklist_items[:half]
        right_col = checklist_items[half:]

        history_rows = []
        for (l_flag, l_label), (r_flag, r_label) in zip(left_col, right_col):
            l_mark = "<b>[X]</b>" if l_flag else "[ ]"
            r_mark = "<b>[X]</b>" if r_flag else "[ ]"
            history_rows.append(
                [
                    Paragraph(l_mark, cell_style),
                    Paragraph(escape(l_label), cell_bold_style if l_flag else cell_style),
                    Paragraph(r_mark, cell_style),
                    Paragraph(escape(r_label), cell_bold_style if r_flag else cell_style),
                ]
            )

        history_table = Table(history_rows, colWidths=[1.0 * cm, 7.7 * cm, 1.0 * cm, 7.7 * cm])
        history_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER),
                    ("BACKGROUND", (0, 0), (0, -1), self.ACCENT_BLUE),
                    ("BACKGROUND", (2, 0), (2, -1), self.ACCENT_BLUE),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 0), (2, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.append(history_table)

        if a.clinical_notes.strip():
            elements.append(Spacer(1, 5))
            elements.append(
                Paragraph(f"<b>Observações Clínicas:</b> {escape(a.clinical_notes.strip())}", body_style)
            )

        # 4. Side-by-side Clinical Images
        if original_image_bytes and gradcam_overlay_bytes:
            elements.append(Paragraph("Registro Fotográfico e Mapeamento da Lesão", section_style))
            img_orig = RLImage(io.BytesIO(original_image_bytes), width=7.5 * cm, height=5.4 * cm)
            img_grad = RLImage(io.BytesIO(gradcam_overlay_bytes), width=7.5 * cm, height=5.4 * cm)
            img_table = Table(
                [
                    [img_orig, img_grad],
                    [
                        Paragraph("<font size=8>Fotografia Intraoral</font>", cell_style),
                        Paragraph(
                            f"<font size=8>Mapeamento de Região ({escape(exam.anatomical_quadrant.value)})</font>",
                            cell_style,
                        ),
                    ],
                ],
                colWidths=[8.7 * cm, 8.7 * cm],
            )
            img_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            elements.append(img_table)

        # 5. Clinical Assessment & Conduct
        elements.append(Paragraph("Parecer Clínico e Conduta Recomendada", section_style))
        for line in exam.clinical_report.markdown_body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                heading_text = re.sub(r"^#+\s*", "", stripped)
                # Keep clinical headings natural
                heading_text = heading_text.replace("(SLM)", "").strip()
                elements.append(Paragraph(f"<b>{escape(heading_text)}</b>", section_style))
            else:
                cleaned = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escape(stripped))
                cleaned = cleaned.replace("`", "")
                elements.append(Paragraph(cleaned, body_style))
                elements.append(Spacer(1, 2))

        # 6. Centered Medical Signature Block (lower on the page)
        sig_center_style = ParagraphStyle(
            "SigCenter",
            parent=body_style,
            alignment=TA_CENTER,
            leading=13,
        )
        sig_sub_style = ParagraphStyle(
            "SigSub",
            parent=cell_style,
            alignment=TA_CENTER,
            textColor=self.MUTED,
        )
        sig_table = Table(
            [
                [Paragraph("____________________________________________________", sig_center_style)],
                [Paragraph(f"<b>{escape(doctor_name)}</b>", sig_center_style)],
                [Paragraph("Médico Responsável — Assinatura / Carimbo", sig_sub_style)],
            ],
            colWidths=[17.4 * cm],
        )
        sig_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(KeepTogether([Spacer(1, 42), sig_table]))

        doc.build(
            elements,
            onFirstPage=self._draw_footer,
            onLaterPages=self._draw_footer,
        )
        return buffer.getvalue()

    def _draw_footer(self, canvas, doc) -> None:
        """Draw institutional footer anchored at the bottom of every page."""
        canvas.saveState()
        page_w, _ = A4
        left_x = doc.leftMargin
        right_x = page_w - doc.rightMargin
        line_y = 1.65 * cm
        text_y = 1.15 * cm

        canvas.setStrokeColor(self.NAVY)
        canvas.setLineWidth(0.8)
        canvas.line(left_x, line_y, right_x, line_y)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(self.MUTED)
        canvas.drawString(left_x, text_y, "contato@oncoscreen.ai")
        canvas.drawCentredString(page_w / 2.0, text_y, "Serviço de Estomatologia e Triagem Clínica")
        canvas.drawRightString(right_x, text_y, "Documento de Apoio Clínico")
        canvas.restoreState()

    def _build_medical_emblem(self) -> Drawing:
        """Draw a clean vector medical cross emblem."""
        d = Drawing(36, 36)
        d.add(Circle(18, 18, 16, fillColor=self.ACCENT_BLUE, strokeColor=self.NAVY, strokeWidth=1))
        d.add(Rect(15, 9, 6, 18, fillColor=self.NAVY, strokeColor=None))
        d.add(Rect(9, 15, 18, 6, fillColor=self.NAVY, strokeColor=None))
        return d
