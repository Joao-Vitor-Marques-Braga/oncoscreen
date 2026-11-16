"""Triage and Exam Pydantic v2 schemas."""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class AnamnesisSchema(BaseModel):
    active_smoking: bool = False
    former_smoker: bool = False
    frequent_alcohol: bool = False
    chronic_sun_exposure: bool = False
    family_cancer_history: bool = False

    evolution_gt_14_days: bool = False
    non_healing_ulcer: bool = False
    leukoplakia: bool = False
    erythroplakia: bool = False
    induration_raised_borders: bool = False
    spontaneous_or_touch_bleeding: bool = False

    local_pain: bool = False
    odynophagia: bool = False
    dysphagia: bool = False
    cervical_lymphadenopathy: bool = False
    recent_weight_loss: bool = False

    clinical_notes: str = Field(default="", max_length=1000)


class GuardrailResponse(BaseModel):
    clinical_score: int
    clinical_risk: str
    cnn_positive: bool
    final_risk: str
    concordance_status: str
    guardrail_triggered: bool
    alert_title: str
    alert_description: str
    triggered_red_flags: List[str]


class TriageResultResponse(BaseModel):
    exam_id: str
    patient_id: str
    patient_name: str
    patient_cpf_masked: str
    cnn_probability: float
    threshold_used: float
    anatomical_quadrant: str
    guardrail: GuardrailResponse
    report_markdown: str
    model_used: str
    generated_via_fallback: bool
    original_image_base64: str
    gradcam_heatmap_base64: str
    gradcam_overlay_base64: str
    inference_time_ms: float
    created_at: datetime


class ExamListItemResponse(BaseModel):
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


class ExamDetailResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    patient_cpf_masked: str
    patient_phone: str
    cnn_probability: float
    threshold_used: float
    anatomical_quadrant: str
    anamnesis: AnamnesisSchema
    selected_anamnesis_labels: List[str]
    guardrail: GuardrailResponse
    report_markdown: str
    model_used: str
    generated_via_fallback: bool
    original_image_base64: str
    gradcam_heatmap_base64: str
    gradcam_overlay_base64: str
    whatsapp_dispatched: bool
    created_at: datetime


class WhatsAppDispatchResponse(BaseModel):
    sent: bool
    fallback_used: bool
    message: str

