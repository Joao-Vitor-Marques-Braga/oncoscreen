"""Execute Multimodal Triage Use Case (Vision CNN + Guardrails + SLM + PDF)."""

from __future__ import annotations

import base64
from uuid import uuid4

from app.application.dtos import ExecuteTriageInputDTO, TriageResultDTO
from app.application.exceptions import NotFoundError, ValidationError
from app.domain.entities.exam import Exam
from app.domain.interfaces.documents import FileStorage, PDFGenerator
from app.domain.interfaces.repositories import ExamRepository, PatientRepository
from app.domain.interfaces.slm_engine import SLMEngine
from app.domain.interfaces.vision_engine import VisionEngine
from app.domain.services.clinical_guardrails import ClinicalGuardrailsService


class ExecuteMultimodalTriageUseCase:
    """Orchestrates CNN + Grad-CAM, Clinical Guardrails, SLM report, and lightweight storage."""

    def __init__(
        self,
        patient_repo: PatientRepository,
        exam_repo: ExamRepository,
        vision_engine: VisionEngine,
        slm_engine: SLMEngine,
        guardrails_service: ClinicalGuardrailsService,
        file_storage: FileStorage,
        pdf_generator: PDFGenerator,
    ) -> None:
        self._patient_repo = patient_repo
        self._exam_repo = exam_repo
        self._vision_engine = vision_engine
        self._slm_engine = slm_engine
        self._guardrails = guardrails_service
        self._storage = file_storage
        self._pdf_generator = pdf_generator

    async def execute(self, data: ExecuteTriageInputDTO) -> TriageResultDTO:
        if not 0.10 <= data.threshold <= 0.90:
            raise ValidationError("O limiar de sensibilidade (threshold) deve estar entre 0.10 e 0.90.")

        patient = await self._patient_repo.get_by_id(data.patient_id)
        if not patient:
            raise NotFoundError("Paciente não encontrado.")

        if not data.image_bytes:
            raise ValidationError("Imagem intraoral obrigatória para triagem.")

        # 1. Run Vision Engine (EfficientNet-B0 + Grad-CAM)
        vision_result = await self._vision_engine.analyze(data.image_bytes)

        # 2. Run Deterministic Clinical Guardrails & Comparative Analysis
        guardrail = self._guardrails.evaluate(
            anamnesis=data.anamnesis,
            cnn_probability=vision_result.probability,
            threshold=data.threshold,
        )

        # 3. Generate Structured Clinical Report via Local SLM (Ollama)
        clinical_report = await self._slm_engine.generate_clinical_report(
            patient_name=patient.full_name,
            cnn_probability=vision_result.probability,
            threshold=data.threshold,
            quadrant=vision_result.anatomical_quadrant,
            anamnesis=data.anamnesis,
            guardrail=guardrail,
        )

        # 4. Persist compressed images in local storage (keep SQLite lightweight)
        exam_id = str(uuid4())
        orig_path = self._storage.save_bytes(
            f"exams/{exam_id}/original.jpg", vision_result.original_jpeg_bytes
        )
        heatmap_path = self._storage.save_bytes(
            f"exams/{exam_id}/heatmap.png", vision_result.heatmap_png_bytes
        )
        overlay_path = self._storage.save_bytes(
            f"exams/{exam_id}/overlay.jpg", vision_result.overlay_jpeg_bytes
        )

        exam = Exam(
            id=exam_id,
            patient_id=patient.id,
            doctor_id=data.doctor_id,
            anamnesis=data.anamnesis,
            cnn_probability=vision_result.probability,
            threshold_used=data.threshold,
            anatomical_quadrant=vision_result.anatomical_quadrant,
            guardrail_assessment=guardrail,
            clinical_report=clinical_report,
            original_image_path=orig_path,
            gradcam_heatmap_path=heatmap_path,
            gradcam_overlay_path=overlay_path,
        )

        # 5. Generate PDF Report and store on disk
        pdf_bytes = self._pdf_generator.generate_exam_pdf(
            exam=exam,
            patient=patient,
            doctor_name=data.doctor_name,
            original_image_bytes=vision_result.original_jpeg_bytes,
            gradcam_overlay_bytes=vision_result.overlay_jpeg_bytes,
        )
        pdf_path = self._storage.save_bytes(f"exams/{exam_id}/laudo_oncoscreen.pdf", pdf_bytes)
        exam.pdf_report_path = pdf_path

        saved_exam = await self._exam_repo.create(exam)

        return TriageResultDTO(
            exam_id=saved_exam.id,
            patient_id=patient.id,
            patient_name=patient.full_name,
            patient_cpf_masked=patient.cpf.masked,
            cnn_probability=saved_exam.cnn_probability,
            threshold_used=saved_exam.threshold_used,
            anatomical_quadrant=saved_exam.anatomical_quadrant.value,
            guardrail=saved_exam.guardrail_assessment,
            report_markdown=saved_exam.clinical_report.markdown_body,
            model_used=saved_exam.clinical_report.model_used,
            generated_via_fallback=saved_exam.clinical_report.generated_via_fallback,
            original_image_base64=base64.b64encode(vision_result.original_jpeg_bytes).decode("ascii"),
            gradcam_heatmap_base64=base64.b64encode(vision_result.heatmap_png_bytes).decode("ascii"),
            gradcam_overlay_base64=base64.b64encode(vision_result.overlay_jpeg_bytes).decode("ascii"),
            inference_time_ms=vision_result.inference_time_ms,
            created_at=saved_exam.created_at,
        )

