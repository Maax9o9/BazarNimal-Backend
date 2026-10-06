from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.di.fastapi import inject
from src.features.adoptions.user.data.dtos.adoption_user_dtos import MyAdoptionRequestDto, PetDto
from src.features.adoptions.user.infrastructure.controllers.adoption_user_controller import AdoptionUserController
from src.features.adoptions.user.infrastructure.validators.adoption_user_validators import (
    CreateAdoptionRequestBody,
    PetListQuery,
)
from src.shared.middlewares.authorize import require_user
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import PaginatedResponse, SuccessResponse, errors
from src.shared.validators.common import PaginationQuery

pets_router = APIRouter(prefix="/pets", tags=["Adopciones"])
requests_router = APIRouter(
    prefix="/adoption-requests",
    tags=["Adopciones"],
    dependencies=[Depends(require_user)],
    responses=errors(401, 403, 422),
)


@pets_router.get("", summary="Listar mascotas (público)", responses=errors(422))
async def list_pets(
    query: Annotated[PetListQuery, Query()],
    controller: AdoptionUserController = inject(AdoptionUserController),
) -> PaginatedResponse[PetDto]:
    return await controller.list_pets(query)


@pets_router.get("/{pet_id}", summary="Detalle de una mascota (público)", responses=errors(404, 422))
async def get_pet(
    pet_id: UUID,
    controller: AdoptionUserController = inject(AdoptionUserController),
) -> SuccessResponse[PetDto]:
    return await controller.get_pet(str(pet_id))


@requests_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar la adopción de una mascota (solo usuarios registrados)",
    responses=errors(404, 409),
)
async def request_adoption(
    body: CreateAdoptionRequestBody,
    user: CurrentUser = Depends(require_user),
    controller: AdoptionUserController = inject(AdoptionUserController),
) -> SuccessResponse[MyAdoptionRequestDto]:
    return await controller.request_adoption(body, user)


@requests_router.get("/me", summary="Mis solicitudes de adopción")
async def my_requests(
    query: Annotated[PaginationQuery, Query()],
    user: CurrentUser = Depends(require_user),
    controller: AdoptionUserController = inject(AdoptionUserController),
) -> PaginatedResponse[MyAdoptionRequestDto]:
    return await controller.my_requests(query, user)


routers = [pets_router, requests_router]
