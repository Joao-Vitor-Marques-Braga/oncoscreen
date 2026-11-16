"""Register or select a patient by CPF before starting triage."""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.application.dtos import PatientSummaryDTO
from app.application.exceptions import ValidationError
from app.domain.entities.patient import Patient
from app.domain.entities.user import User, UserRole
from app.domain.interfaces.repositories import (
    ExamRepository,
    PatientRepository,
    UserRepository,
)
from app.domain.interfaces.security import PasswordHasher
from app.domain.value_objects.cpf import CPF


class RegisterOrSelectPatientByCPFUseCase:
    """Looks up a patient by CPF; registers patient + portal account if missing."""

    def __init__(
        self,
        patient_repo: PatientRepository,
        user_repo: UserRepository,
        exam_repo: ExamRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._patient_repo = patient_repo
        self._user_repo = user_repo
        self._exam_repo = exam_repo
        self._password_hasher = password_hasher

    async def execute(
        self,
        raw_cpf: str,
        full_name: Optional[str] = None,
        birth_date: Optional[date] = None,
        phone_whatsapp: Optional[str] = None,
    ) -> PatientSummaryDTO:
        try:
            cpf = CPF(raw_cpf)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        existing = await self._patient_repo.get_by_cpf(cpf.digits)
        if existing:
            exams = await self._exam_repo.list_by_patient(existing.id)
            return PatientSummaryDTO(
                id=existing.id,
                cpf_formatted=existing.cpf.formatted,
                cpf_masked=existing.cpf.masked,
                full_name=existing.full_name,
                birth_date=existing.birth_date,
                phone_whatsapp=existing.phone_whatsapp,
                created_at=existing.created_at,
                exam_count=len(exams),
                newly_created=False,
            )

        if not full_name or not birth_date or not phone_whatsapp:
            raise ValidationError(
                "Paciente não encontrado. Informe Nome Completo, Data de Nascimento e WhatsApp para cadastrar."
            )

        patient = Patient(
            cpf=cpf,
            full_name=full_name.strip(),
            birth_date=birth_date,
            phone_whatsapp=phone_whatsapp.strip(),
        )
        created_patient = await self._patient_repo.create(patient)

        # Create patient read-only portal credential (password = DDMMYYYY)
        initial_password = birth_date.strftime("%d%m%Y")
        existing_user = await self._user_repo.get_by_email_or_cpf(cpf.digits)
        if not existing_user:
            patient_user = User(
                email_or_cpf=cpf.digits,
                password_hash=self._password_hasher.hash(initial_password),
                full_name=created_patient.full_name,
                role=UserRole.PATIENT,
                patient_id=created_patient.id,
            )
            await self._user_repo.create(patient_user)

        return PatientSummaryDTO(
            id=created_patient.id,
            cpf_formatted=created_patient.cpf.formatted,
            cpf_masked=created_patient.cpf.masked,
            full_name=created_patient.full_name,
            birth_date=created_patient.birth_date,
            phone_whatsapp=created_patient.phone_whatsapp,
            created_at=created_patient.created_at,
            exam_count=0,
            newly_created=True,
            initial_patient_password_hint=f"Data de nascimento (DDMMAAAA): {initial_password}",
        )

