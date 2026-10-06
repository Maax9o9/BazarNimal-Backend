from datetime import datetime

from pydantic import BaseModel

from src.features.adoptions.user.domain.entities.adoption_request import AdoptionRequestStatus
from src.features.adoptions.user.domain.entities.pet import PetSpecies, PetStatus


class PetDto(BaseModel):
    id: str
    name: str
    species: PetSpecies
    breed: str
    age_years: int
    age_months: int
    image_url: str | None
    status: PetStatus


class MyAdoptionRequestPetDto(BaseModel):
    id: str
    name: str
    species: PetSpecies
    image_url: str | None


class MyAdoptionRequestDto(BaseModel):
    id: str
    status: AdoptionRequestStatus
    pet: MyAdoptionRequestPetDto
    created_at: datetime
