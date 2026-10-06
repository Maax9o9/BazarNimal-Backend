from dataclasses import dataclass

from src.core.errors.exceptions import NotFoundError
from src.features.adoptions.admin.domain.entities.pet import Pet, PetData
from src.features.adoptions.admin.domain.repositories.pet_repository import IPetRepository
from src.features.adoptions.admin.domain.usecases.create_pet_usecase import IMAGE_FOLDER
from src.shared.contracts.image_storage import IImageStorage


@dataclass(frozen=True, slots=True)
class UpdatePetInput:
    pet_id: str
    data: PetData
    image: bytes | None  # None conserva la imagen actual


class UpdatePetUseCase:
    def __init__(self, pets: IPetRepository, storage: IImageStorage) -> None:
        self._pets = pets
        self._storage = storage

    async def execute(self, data: UpdatePetInput) -> Pet:
        current = await self._pets.find_by_id(data.pet_id)
        if current is None:
            raise NotFoundError("La mascota no existe")

        new_image_url = await self._storage.save(data.image, IMAGE_FOLDER) if data.image else None
        try:
            updated = await self._pets.update(data.pet_id, data.data, new_image_url or current.image_url)
        except Exception:
            await self._storage.delete(new_image_url)
            raise

        if new_image_url:
            await self._storage.delete(current.image_url)
        return updated
