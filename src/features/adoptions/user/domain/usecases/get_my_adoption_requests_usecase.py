from src.features.adoptions.user.domain.entities.adoption_request import MyAdoptionRequest
from src.features.adoptions.user.domain.repositories.my_adoption_request_repository import (
    IMyAdoptionRequestRepository,
)
from src.shared.types.pagination import Page, PageRequest


class GetMyAdoptionRequestsUseCase:
    def __init__(self, requests: IMyAdoptionRequestRepository) -> None:
        self._requests = requests

    async def execute(self, user_id: str, page: PageRequest) -> Page[MyAdoptionRequest]:
        return await self._requests.list_by_user(user_id, page)
