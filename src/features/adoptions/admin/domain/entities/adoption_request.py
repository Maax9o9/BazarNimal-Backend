from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.features.adoptions.admin.domain.entities.pet import PetStatus


class AdoptionRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Applicant:
    """Datos de contacto del solicitante para que el admin lo llame por teléfono."""

    id: str
    name: str
    email: str
    phone: str | None


@dataclass(frozen=True, slots=True)
class AdoptionRequest:
    id: str
    status: AdoptionRequestStatus
    pet_id: str
    pet_name: str
    pet_status: PetStatus
    applicant: Applicant
    reviewed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AdoptionRequestFilters:
    status: AdoptionRequestStatus | None = None
    pet_id: str | None = None
