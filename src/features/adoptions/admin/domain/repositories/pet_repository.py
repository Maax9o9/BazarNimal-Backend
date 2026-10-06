from abc import ABC, abstractmethod

from src.features.adoptions.admin.domain.entities.pet import Pet, PetData, PetFilters
from src.shared.types.pagination import Page, PageRequest


class IPetRepository(ABC):
    @abstractmethod
    async def create(self, data: PetData, image_url: str, created_by: str) -> Pet: ...

    @abstractmethod
    async def find_by_id(self, pet_id: str) -> Pet | None: ...

    @abstractmethod
    async def list(self, filters: PetFilters, page: PageRequest) -> Page[Pet]: ...

    @abstractmethod
    async def update(self, pet_id: str, data: PetData, image_url: str) -> Pet: ...

    @abstractmethod
    async def soft_delete(self, pet_id: str) -> None:
        """Borra lógicamente la mascota y rechaza sus solicitudes pendientes (una transacción)."""
