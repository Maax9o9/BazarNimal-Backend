from src.features.adoptions.admin.data.dtos.adoption_admin_dtos import PetAdminDto
from src.features.adoptions.admin.data.mappers.adoption_admin_mapper import pet_to_dto
from src.features.adoptions.admin.domain.usecases.create_pet_usecase import CreatePetInput, CreatePetUseCase
from src.features.adoptions.admin.domain.usecases.delete_pet_usecase import DeletePetUseCase
from src.features.adoptions.admin.domain.usecases.get_pet_by_id_usecase import GetPetByIdUseCase
from src.features.adoptions.admin.domain.usecases.get_pets_usecase import GetPetsUseCase
from src.features.adoptions.admin.domain.usecases.update_pet_usecase import UpdatePetInput, UpdatePetUseCase
from src.features.adoptions.admin.infrastructure.validators.adoption_admin_validators import (
    CreatePetForm,
    PetListQuery,
    UpdatePetForm,
)
from src.shared.contracts.image_storage import IImageStorage
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, PaginatedResponse, SuccessResponse, ok, paginated


class PetAdminController:
    def __init__(
        self,
        create_pet: CreatePetUseCase,
        get_pets: GetPetsUseCase,
        get_pet_by_id: GetPetByIdUseCase,
        update_pet: UpdatePetUseCase,
        delete_pet: DeletePetUseCase,
        storage: IImageStorage,
    ) -> None:
        self._create_pet = create_pet
        self._get_pets = get_pets
        self._get_pet_by_id = get_pet_by_id
        self._update_pet = update_pet
        self._delete_pet = delete_pet
        self._storage = storage

    async def create(self, form: CreatePetForm, admin: CurrentUser) -> SuccessResponse[PetAdminDto]:
        pet = await self._create_pet.execute(
            CreatePetInput(data=form.to_domain(), image=await form.image.read(), admin_id=admin.id)
        )
        return ok(pet_to_dto(pet, self._storage), "Mascota registrada")

    async def list(self, query: PetListQuery) -> PaginatedResponse[PetAdminDto]:
        page = await self._get_pets.execute(query.to_filters(), query.to_page_request())
        return paginated([pet_to_dto(pet, self._storage) for pet in page.items], page)

    async def get(self, pet_id: str) -> SuccessResponse[PetAdminDto]:
        return ok(pet_to_dto(await self._get_pet_by_id.execute(pet_id), self._storage))

    async def update(self, pet_id: str, form: UpdatePetForm) -> SuccessResponse[PetAdminDto]:
        image = await form.image.read() if form.image else None
        pet = await self._update_pet.execute(UpdatePetInput(pet_id=pet_id, data=form.to_domain(), image=image))
        return ok(pet_to_dto(pet, self._storage), "Mascota actualizada")

    async def delete(self, pet_id: str) -> MessageResponse:
        await self._delete_pet.execute(pet_id)
        return MessageResponse(message="Mascota eliminada")
