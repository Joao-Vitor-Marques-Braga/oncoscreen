"""Formal clinical PDF report generator using ReportLab."""

from __future__ import annotations

import io
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.domain.entities.exam import Exam
from app.domain.entities.patient import Patient
from app.domain.interfaces.documents import PDFGenerator


class ReportLabPDFGenerator(PDFGenerator):
    """Generates PubMed-inspired clinical triage PDF reports."""

    NAVY = colors.HexColor("#1E3A8A")
    SLATE = colors.HexColor("#0F172A")
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
            topMargin=1.6 * cm,
            bottomMargin=1.6 * cm,
            title=f"Laudo OncoScreen.AI - {patient.full_name}",
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "OncoTitle",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.white,
            spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "OncoSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#E2E8F0"),
        )
        section_style = ParagraphStyle(
            "OncoSection",
            parent=styles["Heading2"],
            fontSize=11,
            textColor=self.NAVY,
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "OncoBody",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13.5,
            textColor=self.SLATE,
        )

        elements: list = []

        # Institutional Header
        header_table = Table(
            [
                [
                    Paragraph("<b>OncoScreen.AI</b> — Sistema Multimodal de Apoio à Decisão Clínica", title_style),
                ],
                [
                    Paragraph("Triagem Precoce de Câncer de Cavidade Oral e Cabeça e Pescoço (HNSCC)", subtitle_style),
                ],
            ],
            colWidths=[17.4 * cm],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.NAVY),
                    ("TOPPADDING", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # Patient & Exam Identification
        g = exam.guardrail_assessment
        info_data = [
            ["Paciente:", escape(patient.full_name), "CPF:", patient.cpf.masked],
            [
                "Data de Nasc.:",
                patient.birth_date.strftime("%d/%m/%Y"),
                "WhatsApp:",
                escape(patient.phone_whatsapp),
            ],
            [
                "Médico Responsável:",
                escape(doctor_name),
                "Data do Exame:",
                exam.created_at.strftime("%d/%m/%Y %H:%M UTC"),
            ],
            [
                "Risco Final:",
                escape(g.final_risk.value),
                "Probabilidade CNN:",
                f"{exam.cnn_probability:.1%} (Limiar: {exam.threshold_used:.0%})",
            ],
            [
                "Localização Grad-CAM:",
                escape(exam.anatomical_quadrant.value),
                "Escore Clínico:",
                f"{g.clinical_score} pts ({g.clinical_risk.value})",
            ],
        ]
        info_table = Table(info_data, colWidths=[3.4 * cm, 5.5 * cm, 3.3 * cm, 5.2 * cm])
        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.BG_LIGHT),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.SLATE),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(info_table)
        elements.append(Spacer(1, 8))

        # Guardrail Banner
        elements.append(Paragraph(f"<b>{escape(g.alert_title)}</b>", section_style))
        elements.append(Paragraph(escape(g.alert_description), body_style))

        # Anamnesis Summary
        elements.append(Paragraph("Resumo da Anamnese Estruturada", section_style))
        selected = exam.anamnesis.selected_labels()
        anamnesis_text = ", ".join(selected) if selected else "Nenhum fator de risco ou sintoma marcado."
        elements.append(Paragraph(escape(anamnesis_text), body_style))
        if exam.anamnesis.clinical_notes.strip():
            elements.append(
                Paragraph(f"<b>Observações:</b> {escape(exam.anamnesis.clinical_notes.strip())}", body_style)
            )

        # Side-by-side Images
        if original_image_bytes and gradcam_overlay_bytes:
            elements.append(Paragraph("Análise Visual Intraoral e Mapa de Ativação Grad-CAM", section_style))
            img_orig = RLImage(io.BytesIO(original_image_bytes), width=7.8 * cm, height=5.8 * cm)
            img_grad = RLImage(io.BytesIO(gradcam_overlay_bytes), width=7.8 * cm, height=5.8 * cm)
            img_table = Table(
                [
                    [img_orig, img_grad],
                    [
                        Paragraph("<font size=8>Imagem Intraoral Original</font>", body_style),
                        Paragraph(
                            f"<font size=8>Sobreposição Grad-CAM ({escape(exam.anatomical_quadrant.value)})</font>",
                            body_style,
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
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(img_table)

        # SLM Structured Clinical Report
        elements.append(Paragraph("Laudo Clínico Estruturado (SLM)", section_style))
        for line in exam.clinical_report.markdown_body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                heading_text = re.sub(r"^#+\s*", "", stripped)
                elements.append(Paragraph(f"<b>{escape(heading_text)}</b>", section_style))
            else:
                cleaned = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escape(stripped))
                cleaned = cleaned.replace("`", "")
                elements.append(Paragraph(cleaned, body_style))
                elements.append(Spacer(1, 2))

        elements.append(Spacer(1, 10))
        elements.append(
            Paragraph(
                "<font size=7.5 color='#64748B'>Aviso Clínico: O OncoScreen.AI é um Sistema de Apoio à Decisão Clínica (CDSS) "
                "destinado à triagem precoce. Não substitui a avaliação presencial e o exame anatomopatológico (biópsia).</font>",
                body_style,
            )
        )

        doc.build(elements)
        return buffer.getvalue()

