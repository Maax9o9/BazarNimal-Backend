from src.core.errors.exceptions import ConflictError, NotFoundError
from src.features.adoptions.admin.domain.entities.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.features.adoptions.admin.domain.repositories.adoption_request_repository import IAdoptionRequestRepository


class RejectAdoptionRequestUseCase:
    def __init__(self, requests: IAdoptionRequestRepository) -> None:
        self._requests = requests

    async def execute(self, request_id: str, admin_id: str) -> AdoptionRequest:
        request = await self._requests.find_by_id(request_id)
        if request is None:
            raise NotFoundError("La solicitud de adopción no existe")
        if request.status is not AdoptionRequestStatus.PENDING:
            raise ConflictError("Solo se pueden rechazar solicitudes pendientes")

        await self._requests.reject(request.id, admin_id)
        rejected = await self._requests.find_by_id(request.id)
        assert rejected is not None
        return rejected
