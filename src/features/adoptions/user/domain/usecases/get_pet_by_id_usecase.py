from src.core.errors.exceptions import NotFoundError
from src.features.adoptions.user.domain.entities.pet import Pet
from src.features.adoptions.user.domain.repositories.pet_catalog_repository import IPetCatalogRepository


class GetPetByIdUseCase:
    def __init__(self, pets: IPetCatalogRepository) -> None:
        self._pets = pets

    async def execute(self, pet_id: str) -> Pet:
        pet = await self._pets.find_by_id(pet_id)
        if pet is None:
            raise NotFoundError("La mascota no existe")
        return pet
