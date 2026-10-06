from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, status

from src.core.di.fastapi import inject
from src.features.adoptions.admin.data.dtos.adoption_admin_dtos import AdoptionRequestAdminDto, PetAdminDto
from src.features.adoptions.admin.infrastructure.controllers.adoption_request_admin_controller import (
    AdoptionRequestAdminController,
)
from src.features.adoptions.admin.infrastructure.controllers.pet_admin_controller import PetAdminController
from src.features.adoptions.admin.infrastructure.validators.adoption_admin_validators import (
    AdoptionRequestListQuery,
    CreatePetForm,
    PetListQuery,
    UpdatePetForm,
)
from src.shared.middlewares.authorize import require_admin
from src.shared.middlewares.rate_limit import by_user, rate_limit
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, PaginatedResponse, SuccessResponse, errors
from src.shared.validators.image import MULTIPART

ADMIN_ERRORS = errors(401, 403, 422)

pets_router = APIRouter(
    prefix="/admin/pets",
    tags=["Admin - Adopciones"],
    dependencies=[Depends(require_admin)],
    responses=ADMIN_ERRORS,
)
requests_router = APIRouter(
    prefix="/admin/adoption-requests",
    tags=["Admin - Adopciones"],
    dependencies=[Depends(require_admin)],
    responses=ADMIN_ERRORS,
)


@pets_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar mascota en adopción",
    responses=errors(429),
    dependencies=[Depends(rate_limit("upload", by_user))],
)
async def create_pet(
    form: Annotated[CreatePetForm, Form(media_type=MULTIPART)],
    admin: CurrentUser = Depends(require_admin),
    controller: PetAdminController = inject(PetAdminController),
) -> SuccessResponse[PetAdminDto]:
    return await controller.create(form, admin)


@pets_router.get("", summary="Listar mascotas (todas las de adopción y adoptadas)")
async def list_pets(
    query: Annotated[PetListQuery, Query()],
    controller: PetAdminController = inject(PetAdminController),
) -> PaginatedResponse[PetAdminDto]:
    return await controller.list(query)


@pets_router.get("/{pet_id}", summary="Detalle de una mascota", responses=errors(404))
async def get_pet(
    pet_id: UUID,
    controller: PetAdminController = inject(PetAdminController),
) -> SuccessResponse[PetAdminDto]:
    return await controller.get(str(pet_id))


@pets_router.put(
    "/{pet_id}",
    summary="Actualizar mascota (la imagen es opcional)",
    responses=errors(404, 429),
    dependencies=[Depends(rate_limit("upload", by_user))],
)
async def update_pet(
    pet_id: UUID,
    form: Annotated[UpdatePetForm, Form(media_type=MULTIPART)],
    controller: PetAdminController = inject(PetAdminController),
) -> SuccessResponse[PetAdminDto]:
    return await controller.update(str(pet_id), form)


@pets_router.delete("/{pet_id}", summary="Eliminar mascota", responses=errors(404))
async def delete_pet(
    pet_id: UUID,
    controller: PetAdminController = inject(PetAdminController),
) -> MessageResponse:
    return await controller.delete(str(pet_id))


@requests_router.get("", summary="Listar solicitudes de adopción con los datos de contacto del usuario")
async def list_requests(
    query: Annotated[AdoptionRequestListQuery, Query()],
    controller: AdoptionRequestAdminController = inject(AdoptionRequestAdminController),
) -> PaginatedResponse[AdoptionRequestAdminDto]:
    return await controller.list(query)


@requests_router.get("/{request_id}", summary="Detalle de una solicitud", responses=errors(404))
async def get_request(
    request_id: UUID,
    controller: AdoptionRequestAdminController = inject(AdoptionRequestAdminController),
) -> SuccessResponse[AdoptionRequestAdminDto]:
    return await controller.get(str(request_id))


@requests_router.patch(
    "/{request_id}/approve",
    summary="Aprobar solicitud (la mascota pasa a adoptada y se rechazan las demás pendientes)",
    responses=errors(404, 409),
)
async def approve_request(
    request_id: UUID,
    admin: CurrentUser = Depends(require_admin),
    controller: AdoptionRequestAdminController = inject(AdoptionRequestAdminController),
) -> SuccessResponse[AdoptionRequestAdminDto]:
    return await controller.approve(str(request_id), admin)


@requests_router.patch("/{request_id}/reject", summary="Rechazar solicitud", responses=errors(404, 409))
async def reject_request(
    request_id: UUID,
    admin: CurrentUser = Depends(require_admin),
    controller: AdoptionRequestAdminController = inject(AdoptionRequestAdminController),
) -> SuccessResponse[AdoptionRequestAdminDto]:
    return await controller.reject(str(request_id), admin)


routers = [pets_router, requests_router]
