"""Abstract Vision Engine contract for CNN inference + Grad-CAM."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.value_objects.anatomical_quadrant import AnatomicalQuadrant


@dataclass(frozen=True)
class VisionAnalysisResult:
    """Output produced by the Vision Engine."""

    probability: float
    anatomical_quadrant: AnatomicalQuadrant
    original_jpeg_bytes: bytes
    heatmap_png_bytes: bytes
    overlay_jpeg_bytes: bytes
    inference_time_ms: float


class VisionEngine(ABC):
    """Port for intraoral image classification and Grad-CAM generation."""

    @abstractmethod
    async def analyze(self, image_bytes: bytes) -> VisionAnalysisResult:
        """Run CNN inference and Grad-CAM localization on raw image bytes."""

    @abstractmethod
    def status(self) -> dict[str, object]:
        """Return runtime diagnostics (device, threads, weights loaded)."""

