"""Internal Data Transfer Objects (DTOs) for application use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.clinical_report import GuardrailAssessment
from app.domain.entities.user import UserRole


@dataclass(frozen=True)
class AuthTokenDTO:
    access_token: str
    token_type: str
    user_id: str
    full_name: str
    role: UserRole
    patient_id: Optional[str] = None


@dataclass(frozen=True)
class PatientSummaryDTO:
    id: str
    cpf_formatted: str
    cpf_masked: str
    full_name: str
    birth_date: date
    phone_whatsapp: str
    created_at: datetime
    exam_count: int
    newly_created: bool = False
    initial_patient_password_hint: Optional[str] = None


@dataclass(frozen=True)
class ExecuteTriageInputDTO:
    patient_id: str
    doctor_id: str
    doctor_name: str
    image_bytes: bytes
    threshold: float
    anamnesis: Anamnesis


@dataclass(frozen=True)
class TriageResultDTO:
    exam_id: str
    patient_id: str
    patient_name: str
    patient_cpf_masked: str
    cnn_probability: float
    threshold_used: float
    anatomical_quadrant: str
    guardrail: GuardrailAssessment
    report_markdown: str
    model_used: str
    generated_via_fallback: bool
    original_image_base64: str
    gradcam_heatmap_base64: str
    gradcam_overlay_base64: str
    inference_time_ms: float
    created_at: datetime


@dataclass(frozen=True)
class ExamListItemDTO:
    id: str
    patient_id: str
    patient_name: str
    patient_cpf_masked: str
    cnn_probability: float
    threshold_used: float
    final_risk: str
    concordance_status: str
    anatomical_quadrant: str
    whatsapp_dispatched: bool
    created_at: datetime


@dataclass(frozen=True)
class ExamDetailDTO:
    id: str
    patient_id: str
    patient_name: str
    patient_cpf_masked: str
    patient_phone: str
    cnn_probability: float
    threshold_used: float
    anatomical_quadrant: str
    anamnesis: Anamnesis
    selected_anamnesis_labels: List[str]
    guardrail: GuardrailAssessment
    report_markdown: str
    model_used: str
    generated_via_fallback: bool
    original_image_base64: str
    gradcam_heatmap_base64: str
    gradcam_overlay_base64: str
    whatsapp_dispatched: bool
    created_at: datetime


@dataclass(frozen=True)
class SystemMetricsDTO:
    total_exams: int
    total_patients: int
    risk_distribution: dict[str, int]
    concordance_distribution: dict[str, int]
    guardrail_activations: int
    average_cnn_probability: float
    estimated_roc_auc: float
    estimated_sensitivity: float
    estimated_specificity: float

