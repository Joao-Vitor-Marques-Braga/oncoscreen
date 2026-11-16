"""Concrete SQLAlchemy repository implementations."""

from __future__ import annotations

from dataclasses import asdict
from typing import List, Optional

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.clinical_report import ClinicalReport, GuardrailAssessment
from app.domain.entities.exam import Exam
from app.domain.entities.patient import Patient
from app.domain.entities.user import User, UserRole
from app.domain.interfaces.repositories import ExamRepository, PatientRepository, UserRepository
from app.domain.value_objects.anatomical_quadrant import AnatomicalQuadrant
from app.domain.value_objects.cpf import CPF
from app.domain.value_objects.risk_level import ConcordanceStatus, RiskLevel
from app.infrastructure.database.models import ExamModel, PatientModel, UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email_or_cpf(self, identifier: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.email_or_cpf == identifier)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            email_or_cpf=user.email_or_cpf,
            password_hash=user.password_hash,
            full_name=user.full_name,
            role=user.role.value,
            patient_id=user.patient_id,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        return user

    @staticmethod
    def _to_entity(row: UserModel) -> User:
        return User(
            id=row.id,
            email_or_cpf=row.email_or_cpf,
            password_hash=row.password_hash,
            full_name=row.full_name,
            role=UserRole(row.role),
            patient_id=row.patient_id,
            is_active=row.is_active,
            created_at=row.created_at,
        )


class SQLAlchemyPatientRepository(PatientRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_cpf(self, cpf_digits: str) -> Optional[Patient]:
        stmt = select(PatientModel).where(PatientModel.cpf == cpf_digits)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        stmt = select(PatientModel).where(PatientModel.id == patient_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def create(self, patient: Patient) -> Patient:
        model = PatientModel(
            id=patient.id,
            cpf=patient.cpf.digits,
            full_name=patient.full_name,
            birth_date=patient.birth_date,
            phone_whatsapp=patient.phone_whatsapp,
            created_at=patient.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        return patient

    async def list_all(self, limit: int = 100) -> List[Patient]:
        stmt = select(PatientModel).order_by(desc(PatientModel.created_at)).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: PatientModel) -> Patient:
        return Patient(
            id=row.id,
            cpf=CPF(row.cpf),
            full_name=row.full_name,
            birth_date=row.birth_date,
            phone_whatsapp=row.phone_whatsapp,
            created_at=row.created_at,
        )


class SQLAlchemyExamRepository(ExamRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, exam: Exam) -> Exam:
        g = exam.guardrail_assessment
        model = ExamModel(
            id=exam.id,
            patient_id=exam.patient_id,
            doctor_id=exam.doctor_id,
            anamnesis_json=asdict(exam.anamnesis),
            cnn_probability=exam.cnn_probability,
            threshold_used=exam.threshold_used,
            anatomical_quadrant=exam.anatomical_quadrant.value,
            clinical_score=g.clinical_score,
            clinical_risk=g.clinical_risk.value,
            cnn_positive=g.cnn_positive,
            final_risk=g.final_risk.value,
            concordance_status=g.concordance_status.value,
            guardrail_triggered=g.guardrail_triggered,
            alert_title=g.alert_title,
            alert_description=g.alert_description,
            triggered_red_flags_json=g.triggered_red_flags,
            report_markdown=exam.clinical_report.markdown_body,
            model_used=exam.clinical_report.model_used,
            generated_via_fallback=exam.clinical_report.generated_via_fallback,
            original_image_path=exam.original_image_path,
            gradcam_heatmap_path=exam.gradcam_heatmap_path,
            gradcam_overlay_path=exam.gradcam_overlay_path,
            pdf_report_path=exam.pdf_report_path,
            whatsapp_dispatched=exam.whatsapp_dispatched,
            created_at=exam.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        return exam

    async def get_by_id(self, exam_id: str) -> Optional[Exam]:
        stmt = select(ExamModel).where(ExamModel.id == exam_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def list_by_patient(self, patient_id: str) -> List[Exam]:
        stmt = (
            select(ExamModel)
            .where(ExamModel.patient_id == patient_id)
            .order_by(desc(ExamModel.created_at))
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_entity(r) for r in rows]

    async def list_all(self, limit: int = 100) -> List[Exam]:
        stmt = select(ExamModel).order_by(desc(ExamModel.created_at)).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_entity(r) for r in rows]

    async def update_pdf_and_whatsapp(
        self,
        exam_id: str,
        pdf_path: Optional[str] = None,
        whatsapp_dispatched: Optional[bool] = None,
    ) -> None:
        values: dict[str, object] = {}
        if pdf_path is not None:
            values["pdf_report_path"] = pdf_path
        if whatsapp_dispatched is not None:
            values["whatsapp_dispatched"] = whatsapp_dispatched
        if values:
            stmt = update(ExamModel).where(ExamModel.id == exam_id).values(**values)
            await self._session.execute(stmt)
            await self._session.commit()

    @staticmethod
    def _to_entity(row: ExamModel) -> Exam:
        anamnesis = Anamnesis(**row.anamnesis_json)
        guardrail = GuardrailAssessment(
            clinical_score=row.clinical_score,
            clinical_risk=RiskLevel(row.clinical_risk),
            cnn_positive=row.cnn_positive,
            final_risk=RiskLevel(row.final_risk),
            concordance_status=ConcordanceStatus(row.concordance_status),
            guardrail_triggered=row.guardrail_triggered,
            alert_title=row.alert_title,
            alert_description=row.alert_description,
            triggered_red_flags=list(row.triggered_red_flags_json or []),
        )
        report = ClinicalReport(
            markdown_body=row.report_markdown,
            model_used=row.model_used,
            generated_via_fallback=row.generated_via_fallback,
        )
        return Exam(
            id=row.id,
            patient_id=row.patient_id,
            doctor_id=row.doctor_id,
            anamnesis=anamnesis,
            cnn_probability=row.cnn_probability,
            threshold_used=row.threshold_used,
            anatomical_quadrant=AnatomicalQuadrant(row.anatomical_quadrant),
            guardrail_assessment=guardrail,
            clinical_report=report,
            original_image_path=row.original_image_path,
            gradcam_heatmap_path=row.gradcam_heatmap_path,
            gradcam_overlay_path=row.gradcam_overlay_path,
            pdf_report_path=row.pdf_report_path,
            whatsapp_dispatched=row.whatsapp_dispatched,
            created_at=row.created_at,
        )

