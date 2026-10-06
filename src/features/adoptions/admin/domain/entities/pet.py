from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PetSpecies(StrEnum):
    DOG = "dog"
    CAT = "cat"


class PetStatus(StrEnum):
    IN_ADOPTION = "in_adoption"
    ADOPTED = "adopted"


@dataclass(frozen=True, slots=True)
class PetData:
    name: str
    species: PetSpecies
    breed: str
    age_years: int
    age_months: int
    status: PetStatus


@dataclass(frozen=True, slots=True)
class Pet:
    id: str
    name: str
    species: PetSpecies
    breed: str
    age_years: int
    age_months: int
    image_url: str
    status: PetStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PetFilters:
    species: PetSpecies | None = None
    status: PetStatus | None = None
    search: str | None = None
    sort: str | None = None
