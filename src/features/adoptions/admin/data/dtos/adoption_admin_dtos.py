from datetime import datetime

from pydantic import BaseModel

from src.features.adoptions.admin.domain.entities.adoption_request import AdoptionRequestStatus
from src.features.adoptions.admin.domain.entities.pet import PetSpecies, PetStatus


class PetAdminDto(BaseModel):
    id: str
    name: str
    species: PetSpecies
    breed: str
    age_years: int
    age_months: int
    image_url: str | None
    status: PetStatus
    created_at: datetime
    updated_at: datetime


class ApplicantDto(BaseModel):
    id: str
    name: str
    email: str
    phone: str | None


class AdoptionRequestPetDto(BaseModel):
    id: str
    name: str
    status: PetStatus


class AdoptionRequestAdminDto(BaseModel):
    id: str
    status: AdoptionRequestStatus
    pet: AdoptionRequestPetDto
    applicant: ApplicantDto
    reviewed_at: datetime | None
    created_at: datetime
