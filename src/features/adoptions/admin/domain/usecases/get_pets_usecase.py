from src.features.adoptions.admin.domain.entities.pet import Pet, PetFilters
from src.features.adoptions.admin.domain.repositories.pet_repository import IPetRepository
from src.shared.types.pagination import Page, PageRequest


class GetPetsUseCase:
    def __init__(self, pets: IPetRepository) -> None:
        self._pets = pets

    async def execute(self, filters: PetFilters, page: PageRequest) -> Page[Pet]:
        return await self._pets.list(filters, page)
