from src.features.adoptions.admin.domain.entities.adoption_request import AdoptionRequest, AdoptionRequestFilters
from src.features.adoptions.admin.domain.repositories.adoption_request_repository import IAdoptionRequestRepository
from src.shared.types.pagination import Page, PageRequest


class GetAdoptionRequestsUseCase:
    def __init__(self, requests: IAdoptionRequestRepository) -> None:
        self._requests = requests

    async def execute(self, filters: AdoptionRequestFilters, page: PageRequest) -> Page[AdoptionRequest]:
        return await self._requests.list(filters, page)
