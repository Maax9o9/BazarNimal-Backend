from typing import Literal
from uuid import UUID

from pydantic import Field

from src.features.adoptions.user.domain.entities.pet import PetFilters, PetSpecies, PetStatus
from src.shared.validators.common import PaginationQuery, StrictSchema


class PetListQuery(PaginationQuery):
    species: PetSpecies | None = None
    status: PetStatus | None = None
    search: str | None = Field(default=None, max_length=80)
    sort: Literal["created_at", "-created_at", "name", "-name"] = "-created_at"

    def to_filters(self) -> PetFilters:
        return PetFilters(species=self.species, status=self.status, search=self.search or None, sort=self.sort)


class CreateAdoptionRequestBody(StrictSchema):
    pet_id: UUID
