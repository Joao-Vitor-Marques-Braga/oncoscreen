"""Evolution API WhatsApp adapter with graceful offline fallback."""

from __future__ import annotations

import base64
import logging
import re

import httpx

from app.domain.interfaces.whatsapp_client import WhatsAppClient, WhatsAppDispatchResult

logger = logging.getLogger(__name__)


class EvolutionWhatsAppAdapter(WhatsAppClient):
    """Sends exam summaries and PDF reports via Evolution API REST endpoints."""

    def __init__(self, api_url: str, api_key: str, instance_name: str) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._instance = instance_name

    async def send_exam_report(
        self,
        phone_number: str,
        patient_name: str,
        summary_text: str,
        pdf_bytes: bytes,
        pdf_filename: str,
    ) -> WhatsAppDispatchResult:
        digits = re.sub(r"\D", "", phone_number or "")
        if len(digits) in (10, 11):
            digits = f"55{digits}"

        if not self._api_key or not self._api_url:
            return WhatsAppDispatchResult(
                sent=False,
                fallback_used=True,
                message=(
                    "Evolution API não configurada no ambiente (.env). "
                    "O laudo em PDF está pronto para download manual."
                ),
            )

        b64_pdf = base64.b64encode(pdf_bytes).decode("ascii")
        endpoint = f"{self._api_url}/message/sendMedia/{self._instance}"
        headers = {"apikey": self._api_key, "Content-Type": "application/json"}
        payload = {
            "number": digits,
            "mediatype": "document",
            "mimetype": "application/pdf",
            "caption": summary_text,
            "media": b64_pdf,
            "fileName": pdf_filename,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
            return WhatsAppDispatchResult(
                sent=True,
                fallback_used=False,
                message=f"Laudo enviado com sucesso via WhatsApp para {phone_number}.",
            )
        except Exception as exc:
            logger.warning("Evolution API dispatch failed (%s). Returning graceful fallback.", exc)
            return WhatsAppDispatchResult(
                sent=False,
                fallback_used=True,
                message=(
                    "Gateway WhatsApp (Evolution API) indisponível no momento. "
                    "O laudo PDF foi gerado e pode ser baixado diretamente."
                ),
            )

    async def health_check(self) -> dict[str, object]:
        if not self._api_key:
            return {
                "configured": False,
                "online": False,
                "instance": self._instance,
                "message": "EVOLUTION_API_KEY não definida",
            }
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    f"{self._api_url}/instance/connectionState/{self._instance}",
                    headers={"apikey": self._api_key},
                )
                return {
                    "configured": True,
                    "online": resp.status_code < 400,
                    "instance": self._instance,
                    "status_code": resp.status_code,
                }
        except Exception as exc:
            return {
                "configured": True,
                "online": False,
                "instance": self._instance,
                "error": str(exc),
            }

