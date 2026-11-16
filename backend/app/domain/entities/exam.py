"""Exam domain entity aggregating vision, anamnesis, guardrails, and report."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.clinical_report import ClinicalReport, GuardrailAssessment
from app.domain.value_objects.anatomical_quadrant import AnatomicalQuadrant


@dataclass
class Exam:
    """Complete multimodal triage exam record."""

    patient_id: str
    doctor_id: str
    anamnesis: Anamnesis
    cnn_probability: float
    threshold_used: float
    anatomical_quadrant: AnatomicalQuadrant
    guardrail_assessment: GuardrailAssessment
    clinical_report: ClinicalReport
    original_image_path: str
    gradcam_heatmap_path: str
    gradcam_overlay_path: str
    pdf_report_path: Optional[str] = None
    whatsapp_dispatched: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

