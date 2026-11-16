"""Authentication Pydantic v2 schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=3, description="E-mail (Médico) ou CPF (Paciente)")
    password: str = Field(..., min_length=3)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    full_name: str
    role: str
    patient_id: Optional[str] = None


class CurrentUserResponse(BaseModel):
    user_id: str
    full_name: str
    role: str
    patient_id: Optional[str] = None

