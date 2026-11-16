"""Abstract WhatsApp messaging client contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class WhatsAppDispatchResult:
    """Result of attempting to dispatch an exam report via WhatsApp."""

    sent: bool
    message: str
    fallback_used: bool = False


class WhatsAppClient(ABC):
    """Port for sending clinical reports and PDFs to patients via WhatsApp."""

    @abstractmethod
    async def send_exam_report(
        self,
        phone_number: str,
        patient_name: str,
        summary_text: str,
        pdf_bytes: bytes,
        pdf_filename: str,
    ) -> WhatsAppDispatchResult:
        """Send summary message and PDF attachment via WhatsApp."""

    @abstractmethod
    async def health_check(self) -> dict[str, object]:
        """Check WhatsApp gateway availability."""

