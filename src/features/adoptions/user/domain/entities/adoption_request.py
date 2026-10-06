from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.features.adoptions.user.domain.entities.pet import PetSpecies


class AdoptionRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class MyAdoptionRequest:
    id: str
    status: AdoptionRequestStatus
    pet_id: str
    pet_name: str
    pet_species: PetSpecies
    pet_image_url: str
    created_at: datetime
