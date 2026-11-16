"""Exams history, detail, PDF download, and WhatsApp dispatch endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.application.exceptions import AuthorizationError, NotFoundError
from app.application.use_cases.exams.dispatch_exam_whatsapp import (
    DispatchExamWhatsAppUseCase,
)
from app.application.use_cases.exams.get_exam_detail import GetExamDetailUseCase
from app.application.use_cases.exams.list_exams import ListExamsUseCase
from app.domain.entities.user import UserRole
from app.infrastructure.database.repositories import (
    SQLAlchemyExamRepository,
    SQLAlchemyPatientRepository,
)
from app.presentation.dependencies.container import (
    AppContainer,
    CurrentUserContext,
    get_container,
    get_current_user,
    get_exam_repo,
    get_patient_repo,
    require_doctor,
)
from app.presentation.schemas.triage import (
    AnamnesisSchema,
    ExamDetailResponse,
    ExamListItemResponse,
    GuardrailResponse,
    WhatsAppDispatchResponse,
)

router = APIRouter(prefix="/exams", tags=["Exames e Laudos"])


@router.get("", response_model=List[ExamListItemResponse])
async def list_exams(
    patient_id: Optional[str] = Query(default=None),
    current_user: CurrentUserContext = Depends(get_current_user),
    exam_repo: SQLAlchemyExamRepository = Depends(get_exam_repo),
    patient_repo: SQLAlchemyPatientRepository = Depends(get_patient_repo),
) -> List[ExamListItemResponse]:
    use_case = ListExamsUseCase(exam_repo=exam_repo, patient_repo=patient_repo)
    dtos = await use_case.execute(
        caller_role=current_user.role,
        caller_patient_id=current_user.patient_id,
        filter_patient_id=patient_id,
    )
    return [ExamListItemResponse(**d.__dict__) for d in dtos]


@router.get("/{exam_id}", response_model=ExamDetailResponse)
async def get_exam_detail(
    exam_id: str,
    current_user: CurrentUserContext = Depends(get_current_user),
    exam_repo: SQLAlchemyExamRepository = Depends(get_exam_repo),
    patient_repo: SQLAlchemyPatientRepository = Depends(get_patient_repo),
    container: AppContainer = Depends(get_container),
) -> ExamDetailResponse:
    use_case = GetExamDetailUseCase(
        exam_repo=exam_repo,
        patient_repo=patient_repo,
        file_storage=container.file_storage,
    )
    dto = await use_case.execute(
        exam_id=exam_id,
        caller_role=current_user.role,
        caller_patient_id=current_user.patient_id,
    )
    return ExamDetailResponse(
        id=dto.id,
        patient_id=dto.patient_id,
        patient_name=dto.patient_name,
        patient_cpf_masked=dto.patient_cpf_masked,
        patient_phone=dto.patient_phone,
        cnn_probability=dto.cnn_probability,
        threshold_used=dto.threshold_used,
        anatomical_quadrant=dto.anatomical_quadrant,
        anamnesis=AnamnesisSchema(**asdict(dto.anamnesis)),
        selected_anamnesis_labels=dto.selected_anamnesis_labels,
        guardrail=GuardrailResponse(
            clinical_score=dto.guardrail.clinical_score,
            clinical_risk=dto.guardrail.clinical_risk.value,
            cnn_positive=dto.guardrail.cnn_positive,
            final_risk=dto.guardrail.final_risk.value,
            concordance_status=dto.guardrail.concordance_status.value,
            guardrail_triggered=dto.guardrail.guardrail_triggered,
            alert_title=dto.guardrail.alert_title,
            alert_description=dto.guardrail.alert_description,
            triggered_red_flags=dto.guardrail.triggered_red_flags,
        ),
        report_markdown=dto.report_markdown,
        model_used=dto.model_used,
        generated_via_fallback=dto.generated_via_fallback,
        original_image_base64=dto.original_image_base64,
        gradcam_heatmap_base64=dto.gradcam_heatmap_base64,
        gradcam_overlay_base64=dto.gradcam_overlay_base64,
        whatsapp_dispatched=dto.whatsapp_dispatched,
        created_at=dto.created_at,
    )


@router.get("/{exam_id}/pdf")
async def download_exam_pdf(
    exam_id: str,
    current_user: CurrentUserContext = Depends(get_current_user),
    exam_repo: SQLAlchemyExamRepository = Depends(get_exam_repo),
    patient_repo: SQLAlchemyPatientRepository = Depends(get_patient_repo),
    container: AppContainer = Depends(get_container),
) -> Response:
    exam = await exam_repo.get_by_id(exam_id)
    if not exam:
        raise NotFoundError("Exame não encontrado.")

    if current_user.role == UserRole.PATIENT and exam.patient_id != current_user.patient_id:
        raise AuthorizationError("Acesso negado ao laudo solicitado.")

    if exam.pdf_report_path and container.file_storage.exists(exam.pdf_report_path):
        pdf_bytes = container.file_storage.read_bytes(exam.pdf_report_path)
    else:
        patient = await patient_repo.get_by_id(exam.patient_id)
        if not patient:
            raise NotFoundError("Paciente não encontrado.")
        orig = (
            container.file_storage.read_bytes(exam.original_image_path)
            if container.file_storage.exists(exam.original_image_path)
            else b""
        )
        overlay = (
            container.file_storage.read_bytes(exam.gradcam_overlay_path)
            if container.file_storage.exists(exam.gradcam_overlay_path)
            else b""
        )
        pdf_bytes = container.pdf_generator.generate_exam_pdf(
            exam=exam,
            patient=patient,
            doctor_name=current_user.full_name,
            original_image_bytes=orig,
            gradcam_overlay_bytes=overlay,
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="laudo_oncoscreen_{exam_id[:8]}.pdf"'
        },
    )


@router.post("/{exam_id}/whatsapp", response_model=WhatsAppDispatchResponse)
async def dispatch_exam_whatsapp(
    exam_id: str,
    doctor: CurrentUserContext = Depends(require_doctor),
    exam_repo: SQLAlchemyExamRepository = Depends(get_exam_repo),
    patient_repo: SQLAlchemyPatientRepository = Depends(get_patient_repo),
    container: AppContainer = Depends(get_container),
) -> WhatsAppDispatchResponse:
    use_case = DispatchExamWhatsAppUseCase(
        exam_repo=exam_repo,
        patient_repo=patient_repo,
        file_storage=container.file_storage,
        pdf_generator=container.pdf_generator,
        whatsapp_client=container.whatsapp_client,
    )
    result = await use_case.execute(exam_id=exam_id, doctor_name=doctor.full_name)
    return WhatsAppDispatchResponse(
        sent=result.sent,
        fallback_used=result.fallback_used,
        message=result.message,
    )

