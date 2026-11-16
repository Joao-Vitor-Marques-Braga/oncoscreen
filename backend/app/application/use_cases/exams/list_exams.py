"""List exams with RBAC filtering (Doctor vs. Patient)."""

from __future__ import annotations

from typing import List, Optional

from app.application.dtos import ExamListItemDTO
from app.domain.entities.user import UserRole
from app.domain.interfaces.repositories import ExamRepository, PatientRepository


class ListExamsUseCase:
    """Lists exams scoped by caller role."""

    def __init__(self, exam_repo: ExamRepository, patient_repo: PatientRepository) -> None:
        self._exam_repo = exam_repo
        self._patient_repo = patient_repo

    async def execute(
        self,
        caller_role: UserRole,
        caller_patient_id: Optional[str] = None,
        filter_patient_id: Optional[str] = None,
    ) -> List[ExamListItemDTO]:
        if caller_role == UserRole.PATIENT:
            if not caller_patient_id:
                return []
            exams = await self._exam_repo.list_by_patient(caller_patient_id)
        elif filter_patient_id:
            exams = await self._exam_repo.list_by_patient(filter_patient_id)
        else:
            exams = await self._exam_repo.list_all(limit=100)

        patient_cache: dict[str, tuple[str, str]] = {}
        items: list[ExamListItemDTO] = []

        for exam in exams:
            if exam.patient_id not in patient_cache:
                patient = await self._patient_repo.get_by_id(exam.patient_id)
                if patient:
                    patient_cache[exam.patient_id] = (patient.full_name, patient.cpf.masked)
                else:
                    patient_cache[exam.patient_id] = ("Paciente", "***.***.***-**")

            p_name, p_cpf_masked = patient_cache[exam.patient_id]
            items.append(
                ExamListItemDTO(
                    id=exam.id,
                    patient_id=exam.patient_id,
                    patient_name=p_name,
                    patient_cpf_masked=p_cpf_masked,
                    cnn_probability=exam.cnn_probability,
                    threshold_used=exam.threshold_used,
                    final_risk=exam.guardrail_assessment.final_risk.value,
                    concordance_status=exam.guardrail_assessment.concordance_status.value,
                    anatomical_quadrant=exam.anatomical_quadrant.value,
                    whatsapp_dispatched=exam.whatsapp_dispatched,
                    created_at=exam.created_at,
                )
            )
        return items

