"""Abstract PDF report generator and file storage contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.exam import Exam
from app.domain.entities.patient import Patient


class PDFGenerator(ABC):
    """Port for generating formal clinical PDF reports."""

    @abstractmethod
    def generate_exam_pdf(
        self,
        exam: Exam,
        patient: Patient,
        doctor_name: str,
        original_image_bytes: bytes,
        gradcam_overlay_bytes: bytes,
    ) -> bytes:
        """Render a clinical PDF document and return its bytes."""


class FileStorage(ABC):
    """Port for lightweight local file storage (images and PDFs)."""

    @abstractmethod
    def save_bytes(self, relative_path: str, data: bytes) -> str:
        """Persist bytes under storage root and return the relative path."""

    @abstractmethod
    def read_bytes(self, relative_path: str) -> bytes:
        """Read bytes from a stored relative path."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check whether a stored file exists."""

