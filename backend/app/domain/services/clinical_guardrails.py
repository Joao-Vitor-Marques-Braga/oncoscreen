"""Deterministic Oncological Clinical Guardrails & Comparative Analysis Service."""

from __future__ import annotations

from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.clinical_report import GuardrailAssessment
from app.domain.value_objects.risk_level import ConcordanceStatus, RiskLevel


class ClinicalGuardrailsService:
    """Evaluates contextual clinical risk and cross-checks against CNN vision output."""

    # Weighted clinical scoring for HNSCC / Oral Cavity triage
    _WEIGHTS = {
        "evolution_gt_14_days": 3,
        "erythroplakia": 3,
        "induration_raised_borders": 3,
        "non_healing_ulcer": 3,
        "cervical_lymphadenopathy": 3,
        "active_smoking": 2,
        "frequent_alcohol": 2,
        "leukoplakia": 2,
        "spontaneous_or_touch_bleeding": 2,
        "dysphagia": 2,
        "odynophagia": 2,
        "recent_weight_loss": 2,
        "former_smoker": 1,
        "chronic_sun_exposure": 1,
        "family_cancer_history": 1,
        "local_pain": 1,
    }

    def evaluate(
        self,
        anamnesis: Anamnesis,
        cnn_probability: float,
        threshold: float,
    ) -> GuardrailAssessment:
        """Run deterministic clinical scoring and comparative vision-vs-context analysis."""
        clinical_score = self._compute_score(anamnesis)
        clinical_risk = self._score_to_risk(clinical_score)
        cnn_positive = cnn_probability >= threshold
        red_flags = self._collect_red_flags(anamnesis)

        # Mandatory SUS / Oncological False-Negative Guardrail:
        # Evolution > 14 days + (Active Smoking OR Erythroplakia OR Induration/Raised Borders)
        sus_high_risk_triad = anamnesis.evolution_gt_14_days and (
            anamnesis.active_smoking
            or anamnesis.erythroplakia
            or anamnesis.induration_raised_borders
        )

        # Case 1: High Concordance (CNN positive AND High clinical risk)
        if cnn_positive and clinical_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return GuardrailAssessment(
                clinical_score=clinical_score,
                clinical_risk=clinical_risk,
                cnn_positive=True,
                final_risk=RiskLevel.CRITICAL,
                concordance_status=ConcordanceStatus.HIGH_CONCORDANCE,
                guardrail_triggered=True,
                alert_title="ALERTA CRÍTICO — Concordância Alta (Visão + Contexto Clínico)",
                alert_description=(
                    f"Probabilidade visual ({cnn_probability:.1%}) acima do limiar "
                    f"({threshold:.0%}) em convergência com escore clínico elevado "
                    f"({clinical_score} pts). Encaminhamento prioritário para biópsia / estomatologia."
                ),
                triggered_red_flags=red_flags,
            )

        # Case 2: Critical Discordance (Potential False-Negative from CNN)
        if not cnn_positive and (sus_high_risk_triad or clinical_risk == RiskLevel.HIGH):
            return GuardrailAssessment(
                clinical_score=clinical_score,
                clinical_risk=RiskLevel.HIGH,
                cnn_positive=False,
                final_risk=RiskLevel.HIGH,
                concordance_status=ConcordanceStatus.CRITICAL_DISCORDANCE,
                guardrail_triggered=True,
                alert_title="DISCORDÂNCIA CRÍTICA — Guardrail Oncológico Ativado (Risco de Falso-Negativo)",
                alert_description=(
                    f"Embora a predição visual ({cnn_probability:.1%}) esteja abaixo do limiar "
                    f"({threshold:.0%}), os achados clínicos (ex.: evolução > 14 dias associada a "
                    "fatores de alto risco) elevam compulsoriamente o risco para ALTO."
                ),
                triggered_red_flags=red_flags,
            )

        # Case 3: Visual False-Positive Discordance (CNN positive, but Anamnesis = 0 points)
        if cnn_positive and clinical_score == 0:
            return GuardrailAssessment(
                clinical_score=0,
                clinical_risk=RiskLevel.LOW,
                cnn_positive=True,
                final_risk=RiskLevel.LOW,
                concordance_status=ConcordanceStatus.VISUAL_FALSE_POSITIVE,
                guardrail_triggered=True,
                alert_title=(
                    "DISCORDÂNCIA (Falso-Positivo Visual: CNN > limiar, mas Anamnese = 0 pontos. "
                    "Prevalece o baixo risco clínico)."
                ),
                alert_description=(
                    f"A predição visual ({cnn_probability:.1%}) ficou acima do limiar ({threshold:.0%}), "
                    "mas a anamnese registrou 0 pontos (baixo risco clínico). Possível falso-positivo visual "
                    "(ex.: artefato de iluminação ou instrumento clínico); prevalece o baixo risco clínico."
                ),
                triggered_red_flags=red_flags,
            )

        # Case 4: Visual Alert Only (CNN positive, Low > 0 / Moderate clinical score)
        if cnn_positive:
            elevated = RiskLevel.HIGH if cnn_probability >= max(threshold, 0.75) else RiskLevel.MODERATE
            return GuardrailAssessment(
                clinical_score=clinical_score,
                clinical_risk=clinical_risk,
                cnn_positive=True,
                final_risk=elevated,
                concordance_status=ConcordanceStatus.VISUAL_ALERT_ONLY,
                guardrail_triggered=False,
                alert_title="Alerta Visual — Achado Suspeito na Imagem Intraoral",
                alert_description=(
                    f"A CNN detectou padrão suspeito ({cnn_probability:.1%} ≥ {threshold:.0%}) "
                    f"com escore clínico {clinical_risk.value.lower()} ({clinical_score} pts). "
                    "Recomenda-se correlação clínica presencial detalhada."
                ),
                triggered_red_flags=red_flags,
            )

        # Case 4: Low Concordance (CNN negative and Low/Moderate clinical risk)
        final_risk = RiskLevel.MODERATE if clinical_risk == RiskLevel.MODERATE else RiskLevel.LOW
        return GuardrailAssessment(
            clinical_score=clinical_score,
            clinical_risk=clinical_risk,
            cnn_positive=False,
            final_risk=final_risk,
            concordance_status=ConcordanceStatus.LOW_CONCORDANCE,
            guardrail_triggered=False,
            alert_title="Concordância Baixa — Sem Sinais Críticos Imediatos",
            alert_description=(
                f"Predição visual ({cnn_probability:.1%}) abaixo do limiar ({threshold:.0%}) "
                f"e escore clínico {clinical_risk.value.lower()} ({clinical_score} pts). "
                "Manter acompanhamento clínico de rotina se houver persistência."
            ),
            triggered_red_flags=red_flags,
        )

    def _compute_score(self, anamnesis: Anamnesis) -> int:
        return sum(
            weight
            for attr, weight in self._WEIGHTS.items()
            if getattr(anamnesis, attr, False)
        )

    @staticmethod
    def _score_to_risk(score: int) -> RiskLevel:
        if score >= 7:
            return RiskLevel.HIGH
        if score >= 3:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    @staticmethod
    def _collect_red_flags(anamnesis: Anamnesis) -> list[str]:
        flags: list[str] = []
        if anamnesis.evolution_gt_14_days:
            flags.append("Evolução > 14 dias (Regra SUS)")
        if anamnesis.erythroplakia:
            flags.append("Eritroplasia")
        if anamnesis.induration_raised_borders:
            flags.append("Endurecimento / Bordas elevadas")
        if anamnesis.non_healing_ulcer:
            flags.append("Úlcera que não cicatriza")
        if anamnesis.cervical_lymphadenopathy:
            flags.append("Linfonodomegalia cervical")
        if anamnesis.active_smoking:
            flags.append("Tabagismo ativo")
        return flags

