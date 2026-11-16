"""CPF Value Object with strict Brazilian validation and masking."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CPF:
    """Immutable Brazilian CPF value object."""

    digits: str

    def __init__(self, raw_cpf: str) -> None:
        cleaned = re.sub(r"\D", "", raw_cpf or "")
        if not self._is_valid(cleaned):
            raise ValueError("CPF inválido. Informe 11 dígitos válidos.")
        object.__setattr__(self, "digits", cleaned)

    @staticmethod
    def _is_valid(digits: str) -> bool:
        if len(digits) != 11 or digits == digits[0] * 11:
            return False

        for i in range(9, 11):
            total = sum(int(digits[num]) * ((i + 1) - num) for num in range(i))
            check = ((total * 10) % 11) % 10
            if check != int(digits[i]):
                return False
        return True

    @property
    def formatted(self) -> str:
        """Return CPF formatted as XXX.XXX.XXX-XX."""
        d = self.digits
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"

    @property
    def masked(self) -> str:
        """Return privacy-masked CPF as ***.XXX.XXX-** for clinical PDFs."""
        d = self.digits
        return f"***.{d[3:6]}.{d[6:9]}-**"

    def __str__(self) -> str:
        return self.digits

