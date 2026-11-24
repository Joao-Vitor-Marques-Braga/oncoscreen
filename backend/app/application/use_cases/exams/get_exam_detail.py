"""Get single exam details with RBAC check and Base64 image hydration."""

from __future__ import annotations

import base64
from typing import Optional

from app.application.dtos import ExamDetailDTO
from app.application.exceptions import AuthorizationError, NotFoundError
from app.domain.entities.user import UserRole
from app.domain.interfaces.documents import FileStorage
from app.domain.interfaces.repositories import (
    ExamRepository,
    PatientRepository,
    UserRepository,
)


class GetExamDetailUseCase:
    """Retrieves full exam details and Base64-encoded images from lightweight storage."""

    def __init__(
        self,
        exam_repo: ExamRepository,
        patient_repo: PatientRepository,
        user_repo: UserRepository,
        file_storage: FileStorage,
    ) -> None:
        self._exam_repo = exam_repo
        self._patient_repo = patient_repo
        self._user_repo = user_repo
        self._storage = file_storage

    async def execute(
        self,
        exam_id: str,
        caller_role: UserRole,
        caller_patient_id: Optional[str] = None,
    ) -> ExamDetailDTO:
        exam = await self._exam_repo.get_by_id(exam_id)
        if not exam:
            raise NotFoundError("Exame não encontrado.")

        if caller_role == UserRole.PATIENT and exam.patient_id != caller_patient_id:
            raise AuthorizationError("Acesso negado: você só pode visualizar seus próprios exames.")

        patient = await self._patient_repo.get_by_id(exam.patient_id)
        if not patient:
            raise NotFoundError("Paciente associado ao exame não encontrado.")

        doctor = await self._user_repo.get_by_id(exam.doctor_id)
        doctor_name = doctor.full_name if doctor else "Médico Responsável"

        orig_b64 = self._read_b64(exam.original_image_path)
        heatmap_b64 = self._read_b64(exam.gradcam_heatmap_path)
        overlay_b64 = self._read_b64(exam.gradcam_overlay_path)

        return ExamDetailDTO(
            id=exam.id,
            patient_id=patient.id,
            patient_name=patient.full_name,
            patient_cpf_masked=patient.cpf.masked,
            patient_birth_date=patient.birth_date,
            patient_phone=patient.phone_whatsapp,
            doctor_name=doctor_name,
            cnn_probability=exam.cnn_probability,
            threshold_used=exam.threshold_used,
            anatomical_quadrant=exam.anatomical_quadrant.value,
            anamnesis=exam.anamnesis,
            selected_anamnesis_labels=exam.anamnesis.selected_labels(),
            guardrail=exam.guardrail_assessment,
            report_markdown=exam.clinical_report.markdown_body,
            model_used=exam.clinical_report.model_used,
            generated_via_fallback=exam.clinical_report.generated_via_fallback,
            original_image_base64=orig_b64,
            gradcam_heatmap_base64=heatmap_b64,
            gradcam_overlay_base64=overlay_b64,
            whatsapp_dispatched=exam.whatsapp_dispatched,
            created_at=exam.created_at,
        )

    def _read_b64(self, path: str) -> str:
        if path and self._storage.exists(path):
            return base64.b64encode(self._storage.read_bytes(path)).decode("ascii")
        return ""
