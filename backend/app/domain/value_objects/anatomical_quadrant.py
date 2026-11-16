"""Anatomical quadrant value object for oral cavity Grad-CAM localization."""

from enum import Enum


class AnatomicalQuadrant(str, Enum):
    """Intraoral anatomical quadrants mapped from Grad-CAM peak activation."""

    UPPER_LEFT = "Quadrante Superior Esquerdo"
    UPPER_RIGHT = "Quadrante Superior Direito"
    LOWER_LEFT = "Quadrante Inferior Esquerdo"
    LOWER_RIGHT = "Quadrante Inferior Direito"
    CENTRAL_ANTERIOR = "Região Central / Anterior (Língua/Assoalho)"
    POSTERIOR_OROPHARYNX = "Região Posterior / Orofaringe"

