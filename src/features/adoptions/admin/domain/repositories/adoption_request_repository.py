from abc import ABC, abstractmethod

from src.features.adoptions.admin.domain.entities.adoption_request import AdoptionRequest, AdoptionRequestFilters
from src.shared.types.pagination import Page, PageRequest


class IAdoptionRequestRepository(ABC):
    @abstractmethod
    async def list(self, filters: AdoptionRequestFilters, page: PageRequest) -> Page[AdoptionRequest]: ...

    @abstractmethod
    async def find_by_id(self, request_id: str) -> AdoptionRequest | None: ...

    @abstractmethod
    async def approve(self, request_id: str, pet_id: str, reviewer_id: str) -> None:
        """Aprueba la solicitud, marca la mascota como adoptada y rechaza las demás pendientes."""

    @abstractmethod
    async def reject(self, request_id: str, reviewer_id: str) -> None: ...
