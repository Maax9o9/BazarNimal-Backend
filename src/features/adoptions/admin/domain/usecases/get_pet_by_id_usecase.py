from src.core.errors.exceptions import NotFoundError
from src.features.adoptions.admin.domain.entities.pet import Pet
from src.features.adoptions.admin.domain.repositories.pet_repository import IPetRepository


class GetPetByIdUseCase:
    def __init__(self, pets: IPetRepository) -> None:
        self._pets = pets

    async def execute(self, pet_id: str) -> Pet:
        pet = await self._pets.find_by_id(pet_id)
        if pet is None:
            raise NotFoundError("La mascota no existe")
        return pet
