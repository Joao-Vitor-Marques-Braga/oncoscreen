"""Dispatch exam summary (and optional frontend-generated PDF) via WhatsApp."""

from __future__ import annotations

from typing import Optional

from app.application.exceptions import NotFoundError
from app.domain.interfaces.repositories import ExamRepository, PatientRepository
from app.domain.interfaces.whatsapp_client import WhatsAppClient, WhatsAppDispatchResult


class DispatchExamWhatsAppUseCase:
    """Sends exam summary (and optional PDF from frontend) to patient's WhatsApp."""

    def __init__(
        self,
        exam_repo: ExamRepository,
        patient_repo: PatientRepository,
        whatsapp_client: WhatsAppClient,
    ) -> None:
        self._exam_repo = exam_repo
        self._patient_repo = patient_repo
        self._whatsapp = whatsapp_client

    async def execute(
        self,
        exam_id: str,
        pdf_base64: Optional[str] = None,
    ) -> WhatsAppDispatchResult:
        exam = await self._exam_repo.get_by_id(exam_id)
        if not exam:
            raise NotFoundError("Exame não encontrado.")

        patient = await self._patient_repo.get_by_id(exam.patient_id)
        if not patient:
            raise NotFoundError("Paciente não encontrado.")

        summary = (
            f"*OncoScreen Saúde — Relatório de Avaliação Clínica*\n"
            f"Paciente: {patient.full_name}\n"
            f"Classificação Clínica: *{exam.guardrail_assessment.final_risk.value}*\n"
            f"Região Avaliada: {exam.anatomical_quadrant.value}\n\n"
            f"Acesse o portal do paciente para visualizar o relatório completo."
        )

        result = await self._whatsapp.send_exam_report(
            phone_number=patient.phone_whatsapp,
            patient_name=patient.full_name,
            summary_text=summary,
            pdf_base64=pdf_base64,
            pdf_filename=f"laudo_oncoscreen_{exam.id[:8]}.pdf" if pdf_base64 else None,
        )

        if result.sent:
            await self._exam_repo.mark_whatsapp_dispatched(exam.id)

        return result
