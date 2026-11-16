"""Dispatch exam PDF report via WhatsApp (Evolution API)."""

from __future__ import annotations

from app.application.exceptions import NotFoundError
from app.domain.interfaces.documents import FileStorage, PDFGenerator
from app.domain.interfaces.repositories import ExamRepository, PatientRepository
from app.domain.interfaces.whatsapp_client import WhatsAppClient, WhatsAppDispatchResult


class DispatchExamWhatsAppUseCase:
    """Sends exam summary and PDF attachment to patient's WhatsApp."""

    def __init__(
        self,
        exam_repo: ExamRepository,
        patient_repo: PatientRepository,
        file_storage: FileStorage,
        pdf_generator: PDFGenerator,
        whatsapp_client: WhatsAppClient,
    ) -> None:
        self._exam_repo = exam_repo
        self._patient_repo = patient_repo
        self._storage = file_storage
        self._pdf_generator = pdf_generator
        self._whatsapp = whatsapp_client

    async def execute(self, exam_id: str, doctor_name: str) -> WhatsAppDispatchResult:
        exam = await self._exam_repo.get_by_id(exam_id)
        if not exam:
            raise NotFoundError("Exame não encontrado.")

        patient = await self._patient_repo.get_by_id(exam.patient_id)
        if not patient:
            raise NotFoundError("Paciente não encontrado.")

        if exam.pdf_report_path and self._storage.exists(exam.pdf_report_path):
            pdf_bytes = self._storage.read_bytes(exam.pdf_report_path)
        else:
            orig_bytes = (
                self._storage.read_bytes(exam.original_image_path)
                if self._storage.exists(exam.original_image_path)
                else b""
            )
            overlay_bytes = (
                self._storage.read_bytes(exam.gradcam_overlay_path)
                if self._storage.exists(exam.gradcam_overlay_path)
                else b""
            )
            pdf_bytes = self._pdf_generator.generate_exam_pdf(
                exam=exam,
                patient=patient,
                doctor_name=doctor_name,
                original_image_bytes=orig_bytes,
                gradcam_overlay_bytes=overlay_bytes,
            )
            pdf_path = self._storage.save_bytes(f"exams/{exam.id}/laudo_oncoscreen.pdf", pdf_bytes)
            await self._exam_repo.update_pdf_and_whatsapp(exam.id, pdf_path=pdf_path)

        summary = (
            f"*OncoScreen.AI — Laudo de Triagem Clínica*\n"
            f"Paciente: {patient.full_name}\n"
            f"Classificação de Risco: *{exam.guardrail_assessment.final_risk.value}*\n"
            f"Região Analisada: {exam.anatomical_quadrant.value}\n\n"
            f"Segue em anexo o laudo médico completo em PDF."
        )

        result = await self._whatsapp.send_exam_report(
            phone_number=patient.phone_whatsapp,
            patient_name=patient.full_name,
            summary_text=summary,
            pdf_bytes=pdf_bytes,
            pdf_filename=f"laudo_oncoscreen_{exam.id[:8]}.pdf",
        )

        if result.sent:
            await self._exam_repo.update_pdf_and_whatsapp(exam.id, whatsapp_dispatched=True)

        return result

