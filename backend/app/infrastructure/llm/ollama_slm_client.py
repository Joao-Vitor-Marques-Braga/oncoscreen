"""Ollama Local SLM Client for structured clinical report generation."""

from __future__ import annotations

import logging

import httpx

from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.clinical_report import ClinicalReport, GuardrailAssessment
from app.domain.interfaces.slm_engine import SLMEngine
from app.domain.value_objects.anatomical_quadrant import AnatomicalQuadrant
from app.domain.value_objects.risk_level import RiskLevel

logger = logging.getLogger(__name__)


class OllamaSLMClient(SLMEngine):
    """Async HTTPX client for local Ollama inference (oncoscreen-qwen / qwen2.5:3b)."""

    def __init__(self, base_url: str, model: str, timeout_seconds: int = 60) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds

    async def generate_clinical_report(
        self,
        patient_name: str,
        cnn_probability: float,
        threshold: float,
        quadrant: AnatomicalQuadrant,
        anamnesis: Anamnesis,
        guardrail: GuardrailAssessment,
    ) -> ClinicalReport:
        prompt = self._build_prompt(
            patient_name=patient_name,
            cnn_probability=cnn_probability,
            threshold=threshold,
            quadrant=quadrant,
            anamnesis=anamnesis,
            guardrail=guardrail,
        )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json={
                        "model": self._model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 700,
                        },
                    },
                )
                response.raise_for_status()
                payload = response.json()
                text = (payload.get("response") or "").strip()
                if text:
                    return ClinicalReport(
                        markdown_body=text,
                        model_used=self._model,
                        generated_via_fallback=False,
                    )
        except Exception as exc:
            logger.warning("Ollama unavailable (%s). Using deterministic clinical fallback.", exc)

        fallback_md = self._build_deterministic_fallback(
            patient_name=patient_name,
            cnn_probability=cnn_probability,
            threshold=threshold,
            quadrant=quadrant,
            anamnesis=anamnesis,
            guardrail=guardrail,
        )
        return ClinicalReport(
            markdown_body=fallback_md,
            model_used=f"{self._model} (fallback clínico)",
            generated_via_fallback=True,
        )

    async def health_check(self) -> dict[str, object]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return {
                    "online": True,
                    "base_url": self._base_url,
                    "configured_model": self._model,
                    "available_models": models,
                }
        except Exception as exc:
            return {
                "online": False,
                "base_url": self._base_url,
                "configured_model": self._model,
                "error": str(exc),
            }

    @staticmethod
    def _build_prompt(
        patient_name: str,
        cnn_probability: float,
        threshold: float,
        quadrant: AnatomicalQuadrant,
        anamnesis: Anamnesis,
        guardrail: GuardrailAssessment,
    ) -> str:
        factors = anamnesis.selected_labels()
        factors_str = ", ".join(factors) if factors else "Nenhum fator de risco ou sintoma marcado"
        notes = anamnesis.clinical_notes.strip() or "Sem observações adicionais."

        return (
            "Você é um assistente médico especialista em Estomatologia e Oncologia de Cabeça e Pescoço (HNSCC). "
            "Redija um laudo técnico de triagem em Português (Brasil), em formato Markdown objetivo e científico, "
            "contendo EXATAMENTE as 4 seções: "
            "'## 1. Síntese Diagnóstica', '## 2. Análise Comparativa Imagem vs. Contexto', "
            "'## 3. Estratificação de Risco' e '## 4. Conduta Recomendada'.\n\n"
            f"Dados do Caso:\n"
            f"- Paciente: {patient_name}\n"
            f"- Probabilidade CNN (EfficientNet-B0): {cnn_probability:.1%} (Limiar de corte: {threshold:.0%})\n"
            f"- Localização Grad-CAM predominante: {quadrant.value}\n"
            f"- Escore Clínico da Anamnese: {guardrail.clinical_score} pontos (Risco Clínico: {guardrail.clinical_risk.value})\n"
            f"- Status Comparativo: {guardrail.concordance_status.value} — {guardrail.alert_title}\n"
            f"- Risco Final Consolidado (Guardrail): {guardrail.final_risk.value}\n"
            f"- Fatores/Achados Marcados: {factors_str}\n"
            f"- Observações do Médico: {notes}\n\n"
            "Importante: Se o Guardrail tiver sinalizado discordância crítica (risco de falso-negativo), "
            "destaque explicitamente que a clínica é soberana sobre a visão computacional."
        )

    @staticmethod
    def _build_deterministic_fallback(
        patient_name: str,
        cnn_probability: float,
        threshold: float,
        quadrant: AnatomicalQuadrant,
        anamnesis: Anamnesis,
        guardrail: GuardrailAssessment,
    ) -> str:
        factors = anamnesis.selected_labels()
        factors_md = "\n".join(f"- {item}" for item in factors) if factors else "- Nenhum fator marcado"
        notes = anamnesis.clinical_notes.strip() or "Sem observações adicionais registradas."

        if guardrail.final_risk in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            conduct = (
                "- Encaminhamento **prioritário** para Estomatologia / Cirurgia de Cabeça e Pescoço.\n"
                "- Avaliar realização de **biópsia incisional** da região de maior atividade "
                f"({quadrant.value}) com exame anatomopatológico.\n"
                "- Orientar cessação imediata de tabagismo e etilismo, se aplicável."
            )
        elif guardrail.final_risk == RiskLevel.MODERATE:
            conduct = (
                "- Reavaliação clínica presencial em **7 a 14 dias** para verificar regressão ou persistência da lesão.\n"
                "- Remover possíveis fatores traumáticos locais e solicitar registro fotográfico comparativo.\n"
                "- Caso persista além de 14 dias (Regra SUS), encaminhar para biópsia."
            )
        else:
            conduct = (
                "- Acompanhamento odontológico/clínico de rotina.\n"
                "- Orientar o paciente a retornar imediatamente caso surjam ulcerações persistentes (> 14 dias), "
                "sangramento ou endurecimento local."
            )

        return (
            f"## 1. Síntese Diagnóstica\n"
            f"Triagem multimodal realizada para **{patient_name}**. A rede neural convolucional (`EfficientNet-B0`) "
            f"estimou probabilidade visual de **{cnn_probability:.1%}** (limiar calibrado em **{threshold:.0%}**), "
            f"com foco de ativação Grad-CAM em **{quadrant.value}**.\n\n"
            f"## 2. Análise Comparativa Imagem vs. Contexto\n"
            f"**Parecer do Guardrail:** {guardrail.alert_title}\n\n"
            f"{guardrail.alert_description}\n\n"
            f"**Fatores e achados registrados na anamnese ({guardrail.clinical_score} pts):**\n"
            f"{factors_md}\n\n"
            f"**Observações clínicas:** {notes}\n\n"
            f"## 3. Estratificação de Risco\n"
            f"- **Risco Visual (CNN):** {'Positivo' if guardrail.cnn_positive else 'Negativo'} ({cnn_probability:.1%})\n"
            f"- **Risco Clínico Contextual:** {guardrail.clinical_risk.value}\n"
            f"- **Classificação Final Consolidada:** **{guardrail.final_risk.value}**\n\n"
            f"## 4. Conduta Recomendada\n"
            f"{conduct}\n"
        )

