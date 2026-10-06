from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from src.features.adoptions.admin.domain.entities.adoption_request import AdoptionRequestFilters, AdoptionRequestStatus
from src.features.adoptions.admin.domain.entities.pet import PetData, PetFilters, PetSpecies, PetStatus
from src.shared.validators.common import EmptyAsNone, PaginationQuery, StrictSchema
from src.shared.validators.image import ImageUpload

PetName = Annotated[str, StringConstraints(min_length=1, max_length=80)]
Breed = Annotated[str, StringConstraints(min_length=1, max_length=80)]


class PetFormBase(StrictSchema):
    name: PetName
    species: PetSpecies = Field(description="dog = perro, cat = gato")
    breed: Breed
    age_years: int = Field(ge=0, le=30)
    age_months: int = Field(default=0, ge=0, le=11)
    status: PetStatus = Field(default=PetStatus.IN_ADOPTION, description="in_adoption = en adopción, adopted = adoptado")

    def to_domain(self) -> PetData:
        return PetData(
            name=self.name,
            species=self.species,
            breed=self.breed,
            age_years=self.age_years,
            age_months=self.age_months,
            status=self.status,
        )


class CreatePetForm(PetFormBase):
    image: ImageUpload = Field(description="JPEG, PNG o WEBP")


class UpdatePetForm(PetFormBase):
    image: Annotated[ImageUpload | None, EmptyAsNone] = Field(
        default=None, description="Opcional: si no se envía se conserva la imagen actual"
    )


class PetListQuery(PaginationQuery):
    species: PetSpecies | None = None
    status: PetStatus | None = None
    search: str | None = Field(default=None, max_length=80)
    sort: Literal["created_at", "-created_at", "name", "-name"] = "-created_at"

    def to_filters(self) -> PetFilters:
        return PetFilters(species=self.species, status=self.status, search=self.search or None, sort=self.sort)


class AdoptionRequestListQuery(PaginationQuery):
    status: AdoptionRequestStatus | None = None
    pet_id: UUID | None = None

    def to_filters(self) -> AdoptionRequestFilters:
        return AdoptionRequestFilters(status=self.status, pet_id=str(self.pet_id) if self.pet_id else None)
