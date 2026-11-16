"""System clinical metrics endpoint."""

from fastapi import APIRouter, Depends

from app.application.use_cases.metrics.get_system_metrics import GetSystemMetricsUseCase
from app.infrastructure.database.repositories import (
    SQLAlchemyExamRepository,
    SQLAlchemyPatientRepository,
)
from app.presentation.dependencies.container import (
    CurrentUserContext,
    get_exam_repo,
    get_patient_repo,
    require_doctor,
)
from app.presentation.schemas.settings import SystemMetricsResponse

router = APIRouter(prefix="/metrics", tags=["Métricas Clínicas"])


@router.get("", response_model=SystemMetricsResponse)
async def get_metrics(
    _doctor: CurrentUserContext = Depends(require_doctor),
    exam_repo: SQLAlchemyExamRepository = Depends(get_exam_repo),
    patient_repo: SQLAlchemyPatientRepository = Depends(get_patient_repo),
) -> SystemMetricsResponse:
    use_case = GetSystemMetricsUseCase(exam_repo=exam_repo, patient_repo=patient_repo)
    dto = await use_case.execute()
    return SystemMetricsResponse(**dto.__dict__)

