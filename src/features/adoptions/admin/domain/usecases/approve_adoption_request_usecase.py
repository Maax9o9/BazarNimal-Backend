from src.core.errors.exceptions import ConflictError, NotFoundError
from src.features.adoptions.admin.domain.entities.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.features.adoptions.admin.domain.entities.pet import PetStatus
from src.features.adoptions.admin.domain.repositories.adoption_request_repository import IAdoptionRequestRepository


class ApproveAdoptionRequestUseCase:
    def __init__(self, requests: IAdoptionRequestRepository) -> None:
        self._requests = requests

    async def execute(self, request_id: str, admin_id: str) -> AdoptionRequest:
        request = await self._requests.find_by_id(request_id)
        if request is None:
            raise NotFoundError("La solicitud de adopción no existe")
        if request.status is not AdoptionRequestStatus.PENDING:
            raise ConflictError("Solo se pueden aprobar solicitudes pendientes")
        if request.pet_status is PetStatus.ADOPTED:
            raise ConflictError("La mascota ya fue adoptada")

        await self._requests.approve(request.id, request.pet_id, admin_id)
        approved = await self._requests.find_by_id(request.id)
        assert approved is not None
        return approved
