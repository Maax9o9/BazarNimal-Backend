from dataclasses import dataclass
from enum import StrEnum


class PetSpecies(StrEnum):
    DOG = "dog"
    CAT = "cat"


class PetStatus(StrEnum):
    IN_ADOPTION = "in_adoption"
    ADOPTED = "adopted"


@dataclass(frozen=True, slots=True)
class Pet:
    """Vista pública de una mascota."""

    id: str
    name: str
    species: PetSpecies
    breed: str
    age_years: int
    age_months: int
    image_url: str
    status: PetStatus


@dataclass(frozen=True, slots=True)
class PetFilters:
    species: PetSpecies | None = None
    status: PetStatus | None = None
    search: str | None = None
    sort: str | None = None
