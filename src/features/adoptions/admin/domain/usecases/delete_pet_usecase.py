from src.core.errors.exceptions import NotFoundError
from src.features.adoptions.admin.domain.repositories.pet_repository import IPetRepository
from src.shared.contracts.image_storage import IImageStorage


class DeletePetUseCase:
    def __init__(self, pets: IPetRepository, storage: IImageStorage) -> None:
        self._pets = pets
        self._storage = storage

    async def execute(self, pet_id: str) -> None:
        pet = await self._pets.find_by_id(pet_id)
        if pet is None:
            raise NotFoundError("La mascota no existe")
        await self._pets.soft_delete(pet_id)
        await self._storage.delete(pet.image_url)
