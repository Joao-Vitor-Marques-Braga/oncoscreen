"""Abstract repository contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.exam import Exam
from app.domain.entities.patient import Patient
from app.domain.entities.user import User


class UserRepository(ABC):
    """Port for User persistence."""

    @abstractmethod
    async def get_by_email_or_cpf(self, identifier: str) -> Optional[User]:
        """Find user by email (doctor) or normalized CPF digits (patient)."""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Find user by unique ID."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Persist a new user."""


class PatientRepository(ABC):
    """Port for Patient persistence."""

    @abstractmethod
    async def get_by_cpf(self, cpf_digits: str) -> Optional[Patient]:
        """Find patient by 11-digit CPF."""

    @abstractmethod
    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        """Find patient by ID."""

    @abstractmethod
    async def create(self, patient: Patient) -> Patient:
        """Persist a new patient."""

    @abstractmethod
    async def list_all(self, limit: int = 100) -> List[Patient]:
        """List registered patients."""


class ExamRepository(ABC):
    """Port for Exam persistence."""

    @abstractmethod
    async def create(self, exam: Exam) -> Exam:
        """Persist a completed multimodal triage exam."""

    @abstractmethod
    async def get_by_id(self, exam_id: str) -> Optional[Exam]:
        """Retrieve a single exam by ID."""

    @abstractmethod
    async def list_by_patient(self, patient_id: str) -> List[Exam]:
        """List exams belonging to a specific patient."""

    @abstractmethod
    async def list_all(self, limit: int = 100) -> List[Exam]:
        """List all exams ordered by most recent."""

    @abstractmethod
    async def update_pdf_and_whatsapp(
        self,
        exam_id: str,
        pdf_path: Optional[str] = None,
        whatsapp_dispatched: Optional[bool] = None,
    ) -> None:
        """Update PDF storage path and/or WhatsApp dispatch status."""

