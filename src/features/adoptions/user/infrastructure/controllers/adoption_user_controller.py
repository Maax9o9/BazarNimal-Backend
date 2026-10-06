from src.features.adoptions.user.data.dtos.adoption_user_dtos import MyAdoptionRequestDto, PetDto
from src.features.adoptions.user.data.mappers.adoption_user_mapper import my_request_to_dto, pet_to_dto
from src.features.adoptions.user.domain.usecases.create_adoption_request_usecase import (
    CreateAdoptionRequestUseCase,
)
from src.features.adoptions.user.domain.usecases.get_my_adoption_requests_usecase import (
    GetMyAdoptionRequestsUseCase,
)
from src.features.adoptions.user.domain.usecases.get_pet_by_id_usecase import GetPetByIdUseCase
from src.features.adoptions.user.domain.usecases.get_pets_usecase import GetPetsUseCase
from src.features.adoptions.user.infrastructure.validators.adoption_user_validators import (
    CreateAdoptionRequestBody,
    PetListQuery,
)
from src.shared.contracts.image_storage import IImageStorage
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import PaginatedResponse, SuccessResponse, ok, paginated
from src.shared.validators.common import PaginationQuery


class AdoptionUserController:
    def __init__(
        self,
        get_pets: GetPetsUseCase,
        get_pet_by_id: GetPetByIdUseCase,
        create_request: CreateAdoptionRequestUseCase,
        get_my_requests: GetMyAdoptionRequestsUseCase,
        storage: IImageStorage,
    ) -> None:
        self._get_pets = get_pets
        self._get_pet_by_id = get_pet_by_id
        self._create_request = create_request
        self._get_my_requests = get_my_requests
        self._storage = storage

    async def list_pets(self, query: PetListQuery) -> PaginatedResponse[PetDto]:
        page = await self._get_pets.execute(query.to_filters(), query.to_page_request())
        return paginated([pet_to_dto(pet, self._storage) for pet in page.items], page)

    async def get_pet(self, pet_id: str) -> SuccessResponse[PetDto]:
        return ok(pet_to_dto(await self._get_pet_by_id.execute(pet_id), self._storage))

    async def request_adoption(
        self, body: CreateAdoptionRequestBody, user: CurrentUser
    ) -> SuccessResponse[MyAdoptionRequestDto]:
        request = await self._create_request.execute(user.id, str(body.pet_id))
        return ok(
            my_request_to_dto(request, self._storage),
            "Solicitud enviada. El equipo de BazarNimal te contactará por teléfono.",
        )

    async def my_requests(
        self, query: PaginationQuery, user: CurrentUser
    ) -> PaginatedResponse[MyAdoptionRequestDto]:
        page = await self._get_my_requests.execute(user.id, query.to_page_request())
        return paginated([my_request_to_dto(item, self._storage) for item in page.items], page)
