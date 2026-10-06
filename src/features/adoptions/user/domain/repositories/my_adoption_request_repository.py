from abc import ABC, abstractmethod

from src.features.adoptions.user.domain.entities.adoption_request import MyAdoptionRequest
from src.shared.types.pagination import Page, PageRequest


class IMyAdoptionRequestRepository(ABC):
    @abstractmethod
    async def has_pending(self, user_id: str, pet_id: str) -> bool: ...

    @abstractmethod
    async def create(self, user_id: str, pet_id: str) -> MyAdoptionRequest: ...

    @abstractmethod
    async def list_by_user(self, user_id: str, page: PageRequest) -> Page[MyAdoptionRequest]: ...
