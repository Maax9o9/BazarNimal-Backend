from src.features.adoptions.user.domain.entities.pet import Pet, PetFilters
from src.features.adoptions.user.domain.repositories.pet_catalog_repository import IPetCatalogRepository
from src.shared.types.pagination import Page, PageRequest


class GetPetsUseCase:
    def __init__(self, pets: IPetCatalogRepository) -> None:
        self._pets = pets

    async def execute(self, filters: PetFilters, page: PageRequest) -> Page[Pet]:
        return await self._pets.list(filters, page)
