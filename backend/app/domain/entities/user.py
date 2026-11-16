"""User domain entity and RBAC role definition."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class UserRole(str, Enum):
    """Supported system access roles."""

    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"


@dataclass
class User:
    """Authenticated system user (Doctor or Patient)."""

    email_or_cpf: str
    password_hash: str
    full_name: str
    role: UserRole
    id: str = field(default_factory=lambda: str(uuid4()))
    patient_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

