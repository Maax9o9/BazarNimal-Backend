from src.core.di.container import Container, Lifetime
from src.features.adoptions.admin.data.mappers.adoption_admin_mapper import AdoptionRequestRowMapper
from src.features.adoptions.admin.data.repositories.adoption_request_repository_impl import (
    AdoptionRequestRepositoryImpl,
)
from src.features.adoptions.admin.data.repositories.pet_repository_impl import PetRepositoryImpl
from src.features.adoptions.admin.domain.repositories.adoption_request_repository import IAdoptionRequestRepository
from src.features.adoptions.admin.domain.repositories.pet_repository import IPetRepository
from src.features.adoptions.admin.domain.usecases.approve_adoption_request_usecase import (
    ApproveAdoptionRequestUseCase,
)
from src.features.adoptions.admin.domain.usecases.create_pet_usecase import CreatePetUseCase
from src.features.adoptions.admin.domain.usecases.delete_pet_usecase import DeletePetUseCase
from src.features.adoptions.admin.domain.usecases.get_adoption_request_by_id_usecase import (
    GetAdoptionRequestByIdUseCase,
)
from src.features.adoptions.admin.domain.usecases.get_adoption_requests_usecase import GetAdoptionRequestsUseCase
from src.features.adoptions.admin.domain.usecases.get_pet_by_id_usecase import GetPetByIdUseCase
from src.features.adoptions.admin.domain.usecases.get_pets_usecase import GetPetsUseCase
from src.features.adoptions.admin.domain.usecases.reject_adoption_request_usecase import (
    RejectAdoptionRequestUseCase,
)
from src.features.adoptions.admin.domain.usecases.update_pet_usecase import UpdatePetUseCase
from src.features.adoptions.admin.infrastructure.controllers.adoption_request_admin_controller import (
    AdoptionRequestAdminController,
)
from src.features.adoptions.admin.infrastructure.controllers.pet_admin_controller import PetAdminController


def register(container: Container) -> None:
    container.register(AdoptionRequestRowMapper, lifetime=Lifetime.SINGLETON)
    container.register(IPetRepository, PetRepositoryImpl, lifetime=Lifetime.SCOPED)
    container.register(IAdoptionRequestRepository, AdoptionRequestRepositoryImpl, lifetime=Lifetime.SCOPED)

    for usecase in (
        CreatePetUseCase,
        GetPetsUseCase,
        GetPetByIdUseCase,
        UpdatePetUseCase,
        DeletePetUseCase,
        GetAdoptionRequestsUseCase,
        GetAdoptionRequestByIdUseCase,
        ApproveAdoptionRequestUseCase,
        RejectAdoptionRequestUseCase,
    ):
        container.register(usecase)

    container.register(PetAdminController)
    container.register(AdoptionRequestAdminController)
