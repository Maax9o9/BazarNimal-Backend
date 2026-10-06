from src.core.errors.exceptions import ConflictError, NotFoundError
from src.features.adoptions.user.domain.entities.adoption_request import MyAdoptionRequest
from src.features.adoptions.user.domain.entities.pet import PetStatus
from src.features.adoptions.user.domain.repositories.my_adoption_request_repository import (
    IMyAdoptionRequestRepository,
)
from src.features.adoptions.user.domain.repositories.pet_catalog_repository import IPetCatalogRepository


class CreateAdoptionRequestUseCase:
    def __init__(self, pets: IPetCatalogRepository, requests: IMyAdoptionRequestRepository) -> None:
        self._pets = pets
        self._requests = requests

    async def execute(self, user_id: str, pet_id: str) -> MyAdoptionRequest:
        pet = await self._pets.find_by_id(pet_id)
        if pet is None:
            raise NotFoundError("La mascota no existe")
        if pet.status is not PetStatus.IN_ADOPTION:
            raise ConflictError("Esta mascota ya fue adoptada")
        if await self._requests.has_pending(user_id, pet_id):
            raise ConflictError("Ya tienes una solicitud pendiente para esta mascota")
        return await self._requests.create(user_id, pet_id)
