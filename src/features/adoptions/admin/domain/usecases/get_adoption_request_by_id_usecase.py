from src.core.errors.exceptions import NotFoundError
from src.features.adoptions.admin.domain.entities.adoption_request import AdoptionRequest
from src.features.adoptions.admin.domain.repositories.adoption_request_repository import IAdoptionRequestRepository


class GetAdoptionRequestByIdUseCase:
    def __init__(self, requests: IAdoptionRequestRepository) -> None:
        self._requests = requests

    async def execute(self, request_id: str) -> AdoptionRequest:
        request = await self._requests.find_by_id(request_id)
        if request is None:
            raise NotFoundError("La solicitud de adopción no existe")
        return request
