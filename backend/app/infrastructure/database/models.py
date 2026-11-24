"""SQLAlchemy ORM models mapping domain entities to lightweight SQLite tables."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email_or_cpf: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    patient_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("patients.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PatientModel(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    phone_whatsapp: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExamModel(Base):
    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True, nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Structured Anamnesis stored as compact JSON
    anamnesis_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Vision & Guardrails
    cnn_probability: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_used: Mapped[float] = mapped_column(Float, nullable=False)
    anatomical_quadrant: Mapped[str] = mapped_column(String(100), nullable=False)

    clinical_score: Mapped[int] = mapped_column(Integer, nullable=False)
    clinical_risk: Mapped[str] = mapped_column(String(20), nullable=False)
    cnn_positive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    final_risk: Mapped[str] = mapped_column(String(20), nullable=False)
    concordance_status: Mapped[str] = mapped_column(String(50), nullable=False)
    guardrail_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False)
    alert_title: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_description: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_red_flags_json: Mapped[list] = mapped_column(JSON, nullable=False)

    # SLM Report
    report_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    generated_via_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Lightweight relative paths (binaries stored in backend/storage/)
    original_image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    gradcam_heatmap_path: Mapped[str] = mapped_column(String(255), nullable=False)
    gradcam_overlay_path: Mapped[str] = mapped_column(String(255), nullable=False)

    whatsapp_dispatched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

