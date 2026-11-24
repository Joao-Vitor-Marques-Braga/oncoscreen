"""Clinical risk level and comparative concordance value objects."""

from enum import Enum


class RiskLevel(str, Enum):
    """Stratified clinical risk levels for HNSCC triage."""

    LOW = "BAIXO"
    MODERATE = "MODERADO"
    HIGH = "ALTO"
    CRITICAL = "CRÍTICO"


class ConcordanceStatus(str, Enum):
    """Comparative analysis status between CNN Vision and Clinical Anamnesis."""

    HIGH_CONCORDANCE = "CONCORDANCIA_ALTA"
    CRITICAL_DISCORDANCE = "DISCORDANCIA_CRITICA"
    VISUAL_FALSE_POSITIVE = "DISCORDANCIA_FALSO_POSITIVO"
    VISUAL_ALERT_ONLY = "ALERTA_VISUAL_ISOLADO"
    LOW_CONCORDANCE = "CONCORDANCIA_BAIXA"

