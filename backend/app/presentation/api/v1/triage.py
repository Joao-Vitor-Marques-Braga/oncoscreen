"""Multimodal triage endpoint (Doctor only)."""

from __future__ import annotations

import json
from dataclasses import asdict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.application.dtos import ExecuteTriageInputDTO
from app.application.use_cases.triage.execute_multimodal_triage import (
    ExecuteMultimodalTriageUseCase,
)
from app.domain.entities.anamnesis import Anamnesis
from app.infrastructure.database.repositories import (
    SQLAlchemyExamRepository,
    SQLAlchemyPatientRepository,
)
from app.presentation.dependencies.container import (
    AppContainer,
    CurrentUserContext,
    get_container,
    get_exam_repo,
    get_patient_repo,
    require_doctor,
)
from app.presentation.schemas.triage import (
    AnamnesisSchema,
    GuardrailResponse,
    TriageResultResponse,
)

router = APIRouter(prefix="/triage", tags=["Triagem Multimodal"])


@router.post("/execute", response_model=TriageResultResponse)
async def execute_triage(
    patient_id: str = Form(...),
    threshold: float = Form(0.50),
    anamnesis_json: str = Form(...),
    image: UploadFile = File(...),
    doctor: CurrentUserContext = Depends(require_doctor),
    patient_repo: SQLAlchemyPatientRepository = Depends(get_patient_repo),
    exam_repo: SQLAlchemyExamRepository = Depends(get_exam_repo),
    container: AppContainer = Depends(get_container),
) -> TriageResultResponse:
    try:
        raw_anamnesis = json.loads(anamnesis_json)
        validated_anamnesis = AnamnesisSchema(**raw_anamnesis)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Dados de anamnese inválidos: {exc}",
        ) from exc

    image_bytes = await image.read()
    use_case = ExecuteMultimodalTriageUseCase(
        patient_repo=patient_repo,
        exam_repo=exam_repo,
        vision_engine=container.vision_engine,
        slm_engine=container.slm_engine,
        guardrails_service=container.guardrails_service,
        file_storage=container.file_storage,
    )

    dto = await use_case.execute(
        ExecuteTriageInputDTO(
            patient_id=patient_id,
            doctor_id=doctor.user_id,
            doctor_name=doctor.full_name,
            image_bytes=image_bytes,
            threshold=threshold,
            anamnesis=Anamnesis(**validated_anamnesis.model_dump()),
        )
    )

    return TriageResultResponse(
        exam_id=dto.exam_id,
        patient_id=dto.patient_id,
        patient_name=dto.patient_name,
        patient_cpf_masked=dto.patient_cpf_masked,
        patient_birth_date=dto.patient_birth_date,
        patient_phone=dto.patient_phone,
        doctor_name=dto.doctor_name,
        anamnesis=AnamnesisSchema(**asdict(dto.anamnesis)),
        cnn_probability=dto.cnn_probability,
        threshold_used=dto.threshold_used,
        anatomical_quadrant=dto.anatomical_quadrant,
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
        inference_time_ms=dto.inference_time_ms,
        created_at=dto.created_at,
    )
