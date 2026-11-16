"""Patient lookup and registration endpoints (Doctor only)."""

from typing import List

from fastapi import APIRouter, Depends

from app.application.use_cases.patients.register_or_select_patient import (
    RegisterOrSelectPatientByCPFUseCase,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyExamRepository,
    SQLAlchemyPatientRepository,
    SQLAlchemyUserRepository,
)
from app.presentation.dependencies.container import (
    AppContainer,
    CurrentUserContext,
    get_container,
    get_exam_repo,
    get_patient_repo,
    get_user_repo,
    require_doctor,
)
from app.presentation.schemas.patients import (
    PatientLookupOrRegisterRequest,
    PatientSummaryResponse,
)

router = APIRouter(prefix="/patients", tags=["Pacientes"])


@router.post("/lookup-or-register", response_model=PatientSummaryResponse)
async def lookup_or_register_patient(
    body: PatientLookupOrRegisterRequest,
    _doctor: CurrentUserContext = Depends(require_doctor),
    patient_repo: SQLAlchemyPatientRepository = Depends(get_patient_repo),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repo),
    exam_repo: SQLAlchemyExamRepository = Depends(get_exam_repo),
    container: AppContainer = Depends(get_container),
) -> PatientSummaryResponse:
    use_case = RegisterOrSelectPatientByCPFUseCase(
        patient_repo=patient_repo,
        user_repo=user_repo,
        exam_repo=exam_repo,
        password_hasher=container.password_hasher,
    )
    dto = await use_case.execute(
        raw_cpf=body.cpf,
        full_name=body.full_name,
        birth_date=body.birth_date,
        phone_whatsapp=body.phone_whatsapp,
    )
    return PatientSummaryResponse(**dto.__dict__)


@router.get("", response_model=List[PatientSummaryResponse])
async def list_patients(
    _doctor: CurrentUserContext = Depends(require_doctor),
    patient_repo: SQLAlchemyPatientRepository = Depends(get_patient_repo),
    exam_repo: SQLAlchemyExamRepository = Depends(get_exam_repo),
) -> List[PatientSummaryResponse]:
    patients = await patient_repo.list_all(limit=100)
    results: list[PatientSummaryResponse] = []
    for p in patients:
        exams = await exam_repo.list_by_patient(p.id)
        results.append(
            PatientSummaryResponse(
                id=p.id,
                cpf_formatted=p.cpf.formatted,
                cpf_masked=p.cpf.masked,
                full_name=p.full_name,
                birth_date=p.birth_date,
                phone_whatsapp=p.phone_whatsapp,
                created_at=p.created_at,
                exam_count=len(exams),
                newly_created=False,
            )
        )
    return results

