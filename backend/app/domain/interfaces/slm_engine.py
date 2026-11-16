"""Abstract Small Language Model (SLM) Engine contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.clinical_report import ClinicalReport, GuardrailAssessment
from app.domain.value_objects.anatomical_quadrant import AnatomicalQuadrant


class SLMEngine(ABC):
    """Port for local clinical report generation via SLM (e.g., Ollama)."""

    @abstractmethod
    async def generate_clinical_report(
        self,
        patient_name: str,
        cnn_probability: float,
        threshold: float,
        quadrant: AnatomicalQuadrant,
        anamnesis: Anamnesis,
        guardrail: GuardrailAssessment,
    ) -> ClinicalReport:
        """Generate structured Markdown clinical report from multimodal inputs."""

    @abstractmethod
    async def health_check(self) -> dict[str, object]:
        """Check SLM runtime availability and loaded model."""

