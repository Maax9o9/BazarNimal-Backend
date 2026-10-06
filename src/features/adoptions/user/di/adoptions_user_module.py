from src.core.di.container import Container, Lifetime
from src.features.adoptions.user.data.repositories.my_adoption_request_repository_impl import (
    MyAdoptionRequestRepositoryImpl,
)
from src.features.adoptions.user.data.repositories.pet_catalog_repository_impl import PetCatalogRepositoryImpl
from src.features.adoptions.user.domain.repositories.my_adoption_request_repository import (
    IMyAdoptionRequestRepository,
)
from src.features.adoptions.user.domain.repositories.pet_catalog_repository import IPetCatalogRepository
from src.features.adoptions.user.domain.usecases.create_adoption_request_usecase import (
    CreateAdoptionRequestUseCase,
)
from src.features.adoptions.user.domain.usecases.get_my_adoption_requests_usecase import (
    GetMyAdoptionRequestsUseCase,
)
from src.features.adoptions.user.domain.usecases.get_pet_by_id_usecase import GetPetByIdUseCase
from src.features.adoptions.user.domain.usecases.get_pets_usecase import GetPetsUseCase
from src.features.adoptions.user.infrastructure.controllers.adoption_user_controller import AdoptionUserController


def register(container: Container) -> None:
    container.register(IPetCatalogRepository, PetCatalogRepositoryImpl, lifetime=Lifetime.SCOPED)
    container.register(IMyAdoptionRequestRepository, MyAdoptionRequestRepositoryImpl, lifetime=Lifetime.SCOPED)

    for usecase in (GetPetsUseCase, GetPetByIdUseCase, CreateAdoptionRequestUseCase, GetMyAdoptionRequestsUseCase):
        container.register(usecase)

    container.register(AdoptionUserController)
