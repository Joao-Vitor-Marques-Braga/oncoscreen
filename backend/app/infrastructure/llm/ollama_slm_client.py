"""Ollama Local SLM Client for clean, natural clinical report generation."""

from __future__ import annotations

import logging
import re

import httpx

from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.clinical_report import ClinicalReport, GuardrailAssessment
from app.domain.interfaces.slm_engine import SLMEngine
from app.domain.value_objects.anatomical_quadrant import AnatomicalQuadrant
from app.domain.value_objects.risk_level import RiskLevel

logger = logging.getLogger(__name__)


def sanitize_report_text(raw_text: str) -> str:
    """Remove markdown code fences, raw heading hashes, and broken bullet artifacts."""
    text = raw_text.strip()

    # Strip wrapping ```markdown ... ``` or ``` ... ``` fences
    text = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = re.sub(r"```[a-zA-Z0-9_-]*", "", text)

    # Collapse orphaned bullet lines like "•\nTexto" into "- Texto"
    text = re.sub(r"(?m)^\s*[•●▪]\s*\n+\s*", "- ", text)
    text = re.sub(r"(?m)^\s*[•●▪*]\s+", "- ", text)

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        # Remove backticks and normalize any level of markdown heading (###, ####, #) to clean numbered heading
        stripped = stripped.replace("`", "")
        if re.match(r"^#{1,6}\s+", stripped):
            heading = re.sub(r"^#{1,6}\s+", "", stripped).strip()
            heading = heading.replace("**", "")
            cleaned_lines.append(heading)
        else:
            cleaned_lines.append(stripped.replace("**", ""))

    result = "\n".join(cleaned_lines)
    # Collapse 3+ consecutive newlines
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


class OllamaSLMClient(SLMEngine):
    """Async HTTPX client for local Ollama inference (oncoscreen / qwen2.5:3b)."""

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
                            "num_predict": 650,
                        },
                    },
                )
                response.raise_for_status()
                payload = response.json()
                text = (payload.get("response") or "").strip()
                if text:
                    return ClinicalReport(
                        markdown_body=sanitize_report_text(text),
                        model_used=self._model,
                        generated_via_fallback=False,
                    )
        except Exception as exc:
            logger.warning("Ollama unavailable (%s). Using deterministic clinical fallback.", exc)

        fallback_text = self._build_deterministic_fallback(
            patient_name=patient_name,
            quadrant=quadrant,
            anamnesis=anamnesis,
            guardrail=guardrail,
        )
        return ClinicalReport(
            markdown_body=sanitize_report_text(fallback_text),
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
            "Você é um médico especialista em Estomatologia e Cirurgia de Cabeça e Pescoço. "
            "Redija um relatório clínico formal em Português (Brasil) para constar no prontuário do paciente.\n"
            "REGRAS OBRIGATÓRIAS DE FORMATAÇÃO E CONTEÚDO:\n"
            "- Escreva em texto limpo, SEM blocos de código, SEM ```markdown, SEM símbolos #, SEM asteriscos ** e SEM crases.\n"
            "- NÃO mencione palavras de inteligência artificial (não escreva 'CNN', 'Grad-CAM', 'Guardrail', 'SLM', 'modelo' ou 'algoritmo').\n"
            "- Mantenha o foco exclusivamente em Estomatologia / Cavidade Oral e Cabeça e Pescoço (não invente especialidades não relacionadas como oftalmologia ou siglas incorretas).\n"
            "- Quando o status comparativo indicar falso-positivo visual (anamnese com 0 pontos), explique explicitamente que o achado fotográfico isolado pode corresponder a artefato de iluminação ou instrumento clínico, descartado pela anamnese de baixo risco, prevalecendo o baixo risco clínico.\n"
            "- Use exatamente estas 4 seções em texto simples:\n"
            "1. Síntese Clínica\n"
            "2. Correlação dos Achados\n"
            "3. Estratificação de Risco\n"
            "4. Conduta Recomendada\n\n"
            f"Dados do Atendimento:\n"
            f"- Paciente: {patient_name}\n"
            f"- Índice de suspeita da avaliação fotográfica: {cnn_probability:.1%} (referência: {threshold:.0%})\n"
            f"- Região anatômica avaliada: {quadrant.value}\n"
            f"- Pontuação de anamnese: {guardrail.clinical_score} pontos (Risco clínico: {guardrail.clinical_risk.value})\n"
            f"- Status comparativo: {guardrail.alert_title}\n"
            f"- Classificação final consolidada: {guardrail.final_risk.value}\n"
            f"- Alerta clínico: {guardrail.alert_description}\n"
            f"- Fatores e achados marcados: {factors_str}\n"
            f"- Observações do médico: {notes}\n"
        )

    @staticmethod
    def _build_deterministic_fallback(
        patient_name: str,
        quadrant: AnatomicalQuadrant,
        anamnesis: Anamnesis,
        guardrail: GuardrailAssessment,
    ) -> str:
        factors = anamnesis.selected_labels()
        factors_lines = "\n".join(f"- {item}" for item in factors) if factors else "- Nenhum fator de risco ou sintoma relatado."
        notes = anamnesis.clinical_notes.strip() or "Sem observações adicionais registradas."

        if guardrail.final_risk in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            conduct = (
                "- Encaminhamento prioritário para avaliação especializada em Estomatologia / Cirurgia de Cabeça e Pescoço.\n"
                f"- Avaliar realização de biópsia incisional na região de interesse ({quadrant.value}) para exame anatomopatológico.\n"
                "- Orientar cessação imediata de tabagismo e etilismo, quando aplicável."
            )
        elif guardrail.final_risk == RiskLevel.MODERATE:
            conduct = (
                "- Reavaliação clínica presencial em 7 a 14 dias para verificar regressão ou persistência da alteração observada.\n"
                "- Remover possíveis fatores traumáticos locais e manter acompanhamento fotográfico comparativo.\n"
                "- Caso a lesão persista além de 14 dias, encaminhar para avaliação especializada e biópsia."
            )
        else:
            conduct = (
                "- Acompanhamento odontológico e estomatológico de rotina.\n"
                "- Orientar o paciente a retornar prontamente caso surjam feridas que não cicatrizam em até 14 dias, "
                "sangramento espontâneo ou endurecimento local."
            )

        return (
            f"1. Síntese Clínica\n"
            f"Avaliação clínica intraoral realizada para {patient_name}, com foco principal observado em "
            f"{quadrant.value} e estratificação de risco consolidada como {guardrail.final_risk.value}.\n\n"
            f"2. Correlação dos Achados\n"
            f"Fatores e achados registrados na anamnese ({guardrail.clinical_score} pontos):\n"
            f"{factors_lines}\n"
            f"Observações clínicas: {notes}\n\n"
            f"3. Estratificação de Risco\n"
            f"- Risco Clínico Contextual: {guardrail.clinical_risk.value}\n"
            f"- Classificação Final Consolidada: {guardrail.final_risk.value}\n\n"
            f"4. Conduta Recomendada\n"
            f"{conduct}\n"
        )
