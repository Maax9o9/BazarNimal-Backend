from abc import ABC, abstractmethod

from src.features.adoptions.user.domain.entities.pet import Pet, PetFilters
from src.shared.types.pagination import Page, PageRequest


class IPetCatalogRepository(ABC):
    @abstractmethod
    async def list(self, filters: PetFilters, page: PageRequest) -> Page[Pet]: ...

    @abstractmethod
    async def find_by_id(self, pet_id: str) -> Pet | None: ...
