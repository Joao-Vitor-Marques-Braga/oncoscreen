"""Patient lookup & registration Pydantic v2 schemas."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class PatientLookupOrRegisterRequest(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=14)
    full_name: Optional[str] = Field(default=None, max_length=200)
    birth_date: Optional[date] = None
    phone_whatsapp: Optional[str] = Field(default=None, max_length=30)


class PatientSummaryResponse(BaseModel):
    id: str
    cpf_formatted: str
    cpf_masked: str
    full_name: str
    birth_date: date
    phone_whatsapp: str
    created_at: datetime
    exam_count: int
    newly_created: bool
    initial_patient_password_hint: Optional[str] = None

