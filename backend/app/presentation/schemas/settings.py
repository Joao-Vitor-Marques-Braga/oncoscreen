"""Metrics and Model Settings Pydantic v2 schemas."""

from typing import Any, Dict
from pydantic import BaseModel, Field


class SystemMetricsResponse(BaseModel):
    total_exams: int
    total_patients: int
    risk_distribution: Dict[str, int]
    concordance_distribution: Dict[str, int]
    guardrail_activations: int
    average_cnn_probability: float
    estimated_roc_auc: float
    estimated_sensitivity: float
    estimated_specificity: float


class SystemStatusResponse(BaseModel):
    default_threshold: float
    vision: Dict[str, Any]
    ollama: Dict[str, Any]


class UpdateThresholdRequest(BaseModel):
    default_threshold: float = Field(..., ge=0.10, le=0.90)

