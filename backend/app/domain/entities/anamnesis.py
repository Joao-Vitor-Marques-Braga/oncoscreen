"""Structured clinical anamnesis entity for HNSCC / oral cavity triage."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Anamnesis:
    """Checkbox-oriented structured anamnesis for rapid clinical intake."""

    # Risk Factors
    active_smoking: bool = False
    former_smoker: bool = False
    frequent_alcohol: bool = False
    chronic_sun_exposure: bool = False
    family_cancer_history: bool = False

    # Lesion Characteristics
    evolution_gt_14_days: bool = False
    non_healing_ulcer: bool = False
    leukoplakia: bool = False
    erythroplakia: bool = False
    induration_raised_borders: bool = False
    spontaneous_or_touch_bleeding: bool = False

    # Associated Symptoms
    local_pain: bool = False
    odynophagia: bool = False
    dysphagia: bool = False
    cervical_lymphadenopathy: bool = False
    recent_weight_loss: bool = False

    # Complementary short clinical notes
    clinical_notes: str = ""

    def selected_labels(self) -> list[str]:
        """Return human-readable Portuguese labels for all checked clinical items."""
        mapping = [
            (self.active_smoking, "Tabagismo ativo"),
            (self.former_smoker, "Ex-tabagista"),
            (self.frequent_alcohol, "Etilismo frequente"),
            (self.chronic_sun_exposure, "Exposição solar crônica (lábio)"),
            (self.family_cancer_history, "Histórico familiar de câncer"),
            (self.evolution_gt_14_days, "Evolução > 14 dias (Regra SUS)"),
            (self.non_healing_ulcer, "Úlcera que não cicatriza"),
            (self.leukoplakia, "Mancha branca (Leucoplasia)"),
            (self.erythroplakia, "Mancha vermelha (Eritroplasia)"),
            (self.induration_raised_borders, "Endurecimento / Bordas elevadas"),
            (self.spontaneous_or_touch_bleeding, "Sangramento espontâneo ou ao toque"),
            (self.local_pain, "Dor local"),
            (self.odynophagia, "Odinofagia (dor ao engolir)"),
            (self.dysphagia, "Disfagia"),
            (self.cervical_lymphadenopathy, "Linfonodomegalia cervical palpável"),
            (self.recent_weight_loss, "Perda de peso recente"),
        ]
        return [label for flag, label in mapping if flag]

