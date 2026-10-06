from sqlalchemy import RowMapping

from src.features.adoptions.user.data.dtos.adoption_user_dtos import (
    MyAdoptionRequestDto,
    MyAdoptionRequestPetDto,
    PetDto,
)
from src.features.adoptions.user.domain.entities.adoption_request import AdoptionRequestStatus, MyAdoptionRequest
from src.features.adoptions.user.domain.entities.pet import Pet, PetSpecies, PetStatus
from src.shared.contracts.image_storage import IImageStorage


def row_to_pet(row: RowMapping) -> Pet:
    return Pet(
        id=row["id"],
        name=row["name"],
        species=PetSpecies(row["species"]),
        breed=row["breed"],
        age_years=int(row["age_years"]),
        age_months=int(row["age_months"]),
        image_url=row["image_url"],
        status=PetStatus(row["status"]),
    )


def row_to_my_request(row: RowMapping) -> MyAdoptionRequest:
    return MyAdoptionRequest(
        id=row["id"],
        status=AdoptionRequestStatus(row["status"]),
        pet_id=row["pet_id"],
        pet_name=row["pet_name"],
        pet_species=PetSpecies(row["pet_species"]),
        pet_image_url=row["pet_image_url"],
        created_at=row["created_at"],
    )


def pet_to_dto(pet: Pet, storage: IImageStorage) -> PetDto:
    return PetDto(
        id=pet.id,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        age_years=pet.age_years,
        age_months=pet.age_months,
        image_url=storage.public_url(pet.image_url),
        status=pet.status,
    )


def my_request_to_dto(request: MyAdoptionRequest, storage: IImageStorage) -> MyAdoptionRequestDto:
    return MyAdoptionRequestDto(
        id=request.id,
        status=request.status,
        pet=MyAdoptionRequestPetDto(
            id=request.pet_id,
            name=request.pet_name,
            species=request.pet_species,
            image_url=storage.public_url(request.pet_image_url),
        ),
        created_at=request.created_at,
    )
