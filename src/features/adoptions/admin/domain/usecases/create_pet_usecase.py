from dataclasses import dataclass

from src.features.adoptions.admin.domain.entities.pet import Pet, PetData
from src.features.adoptions.admin.domain.repositories.pet_repository import IPetRepository
from src.shared.contracts.image_storage import IImageStorage

IMAGE_FOLDER = "pets"


@dataclass(frozen=True, slots=True)
class CreatePetInput:
    data: PetData
    image: bytes
    admin_id: str


class CreatePetUseCase:
    def __init__(self, pets: IPetRepository, storage: IImageStorage) -> None:
        self._pets = pets
        self._storage = storage

    async def execute(self, data: CreatePetInput) -> Pet:
        image_url = await self._storage.save(data.image, IMAGE_FOLDER)
        try:
            return await self._pets.create(data.data, image_url, data.admin_id)
        except Exception:
            await self._storage.delete(image_url)
            raise
