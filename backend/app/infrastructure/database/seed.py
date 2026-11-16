"""Initial database seeding for default clinical user."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User, UserRole
from app.domain.interfaces.security import PasswordHasher
from app.infrastructure.database.repositories import SQLAlchemyUserRepository


async def seed_initial_doctor(session: AsyncSession, password_hasher: PasswordHasher) -> None:
    """Create the default doctor account if it does not exist."""
    repo = SQLAlchemyUserRepository(session)
    existing = await repo.get_by_email_or_cpf("doutor@oncoscreen.ai")
    if existing:
        return

    doctor = User(
        email_or_cpf="doutor@oncoscreen.ai",
        password_hash=password_hasher.hash("admin123"),
        full_name="Dr. Carlos Eduardo Mendes (Estomatologia)",
        role=UserRole.DOCTOR,
    )
    await repo.create(doctor)

