"""Unit tests for RegisterOrSelectPatientByCPFUseCase."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

import pytest

from app.application.exceptions import ValidationError
from app.application.use_cases.patients.register_or_select_patient import (
    RegisterOrSelectPatientByCPFUseCase,
)
from app.domain.entities.exam import Exam
from app.domain.entities.patient import Patient
from app.domain.entities.user import User, UserRole
from app.domain.interfaces.repositories import (
    ExamRepository,
    PatientRepository,
    UserRepository,
)
from app.domain.interfaces.security import PasswordHasher


class InMemoryPatientRepo(PatientRepository):
    def __init__(self) -> None:
        self.items: dict[str, Patient] = {}

    async def get_by_cpf(self, cpf_digits: str) -> Optional[Patient]:
        return next((p for p in self.items.values() if p.cpf.digits == cpf_digits), None)

    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        return self.items.get(patient_id)

    async def create(self, patient: Patient) -> Patient:
        self.items[patient.id] = patient
        return patient

    async def list_all(self, limit: int = 100) -> List[Patient]:
        return list(self.items.values())[:limit]


class InMemoryUserRepo(UserRepository):
    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    async def get_by_email_or_cpf(self, identifier: str) -> Optional[User]:
        return next((u for u in self.items.values() if u.email_or_cpf == identifier), None)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        return self.items.get(user_id)

    async def create(self, user: User) -> User:
        self.items[user.id] = user
        return user


class InMemoryExamRepo(ExamRepository):
    async def create(self, exam: Exam) -> Exam:
        return exam

    async def get_by_id(self, exam_id: str) -> Optional[Exam]:
        return None

    async def list_by_patient(self, patient_id: str) -> List[Exam]:
        return []

    async def list_all(self, limit: int = 100) -> List[Exam]:
        return []

    async def update_pdf_and_whatsapp(
        self, exam_id: str, pdf_path: Optional[str] = None, whatsapp_dispatched: Optional[bool] = None
    ) -> None:
        return None


class DummyHasher(PasswordHasher):
    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{plain_password}"


@pytest.mark.asyncio
async def test_register_new_patient_and_select_existing() -> None:
    patient_repo = InMemoryPatientRepo()
    user_repo = InMemoryUserRepo()
    exam_repo = InMemoryExamRepo()
    use_case = RegisterOrSelectPatientByCPFUseCase(
        patient_repo=patient_repo,
        user_repo=user_repo,
        exam_repo=exam_repo,
        password_hasher=DummyHasher(),
    )

    created = await use_case.execute(
        raw_cpf="529.982.247-25",
        full_name="Maria Silva",
        birth_date=date(1980, 5, 12),
        phone_whatsapp="11999998888",
    )
    assert created.newly_created is True
    assert created.cpf_formatted == "529.982.247-25"
    assert created.cpf_masked == "***.982.247-**"

    patient_user = await user_repo.get_by_email_or_cpf("52998224725")
    assert patient_user is not None
    assert patient_user.role == UserRole.PATIENT
    assert patient_user.password_hash == "hashed:12051980"

    selected = await use_case.execute(raw_cpf="52998224725")
    assert selected.newly_created is False
    assert selected.id == created.id


@pytest.mark.asyncio
async def test_invalid_cpf_raises_validation_error() -> None:
    use_case = RegisterOrSelectPatientByCPFUseCase(
        patient_repo=InMemoryPatientRepo(),
        user_repo=InMemoryUserRepo(),
        exam_repo=InMemoryExamRepo(),
        password_hasher=DummyHasher(),
    )
    with pytest.raises(ValidationError):
        await use_case.execute(raw_cpf="111.111.111-11")

