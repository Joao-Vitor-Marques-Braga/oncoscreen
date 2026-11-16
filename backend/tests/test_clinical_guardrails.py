"""Unit tests for ClinicalGuardrailsService (Concordance & False-Negative Guardrails)."""

from app.domain.entities.anamnesis import Anamnesis
from app.domain.services.clinical_guardrails import ClinicalGuardrailsService
from app.domain.value_objects.risk_level import ConcordanceStatus, RiskLevel


def test_high_concordance_triggers_critical_alert() -> None:
    service = ClinicalGuardrailsService()
    anamnesis = Anamnesis(
        active_smoking=True,
        evolution_gt_14_days=True,
        erythroplakia=True,
        induration_raised_borders=True,
    )

    result = service.evaluate(anamnesis=anamnesis, cnn_probability=0.82, threshold=0.50)

    assert result.cnn_positive is True
    assert result.final_risk == RiskLevel.CRITICAL
    assert result.concordance_status == ConcordanceStatus.HIGH_CONCORDANCE
    assert result.guardrail_triggered is True
    assert "CONCORDÂNCIA" in result.alert_title.upper() or "CONCORDANCIA" in result.alert_title.upper()


def test_critical_discordance_false_negative_guardrail_with_smoking() -> None:
    service = ClinicalGuardrailsService()
    anamnesis = Anamnesis(
        evolution_gt_14_days=True,
        active_smoking=True,
    )

    result = service.evaluate(anamnesis=anamnesis, cnn_probability=0.25, threshold=0.50)

    assert result.cnn_positive is False
    assert result.final_risk == RiskLevel.HIGH
    assert result.concordance_status == ConcordanceStatus.CRITICAL_DISCORDANCE
    assert result.guardrail_triggered is True


def test_critical_discordance_false_negative_guardrail_with_erythroplakia() -> None:
    service = ClinicalGuardrailsService()
    anamnesis = Anamnesis(
        evolution_gt_14_days=True,
        erythroplakia=True,
    )

    result = service.evaluate(anamnesis=anamnesis, cnn_probability=0.18, threshold=0.50)

    assert result.cnn_positive is False
    assert result.final_risk == RiskLevel.HIGH
    assert result.concordance_status == ConcordanceStatus.CRITICAL_DISCORDANCE
    assert result.guardrail_triggered is True


def test_visual_alert_only_when_clinical_score_is_low() -> None:
    service = ClinicalGuardrailsService()
    anamnesis = Anamnesis(local_pain=True)

    result = service.evaluate(anamnesis=anamnesis, cnn_probability=0.78, threshold=0.50)

    assert result.cnn_positive is True
    assert result.concordance_status == ConcordanceStatus.VISUAL_ALERT_ONLY
    assert result.final_risk == RiskLevel.HIGH
    assert result.guardrail_triggered is False


def test_low_concordance_when_both_negative() -> None:
    service = ClinicalGuardrailsService()
    anamnesis = Anamnesis()

    result = service.evaluate(anamnesis=anamnesis, cnn_probability=0.12, threshold=0.50)

    assert result.cnn_positive is False
    assert result.final_risk == RiskLevel.LOW
    assert result.concordance_status == ConcordanceStatus.LOW_CONCORDANCE
    assert result.guardrail_triggered is False

