"""Patient domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import uuid4

from app.domain.value_objects.cpf import CPF


@dataclass
class Patient:
    """Clinical patient identified by Brazilian CPF."""

    cpf: CPF
    full_name: str
    birth_date: date
    phone_whatsapp: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

