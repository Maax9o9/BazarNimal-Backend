from sqlalchemy import RowMapping

from src.features.adoptions.admin.data.dtos.adoption_admin_dtos import (
    AdoptionRequestAdminDto,
    AdoptionRequestPetDto,
    ApplicantDto,
    PetAdminDto,
)
from src.features.adoptions.admin.domain.entities.adoption_request import (
    AdoptionRequest,
    AdoptionRequestStatus,
    Applicant,
)
from src.features.adoptions.admin.domain.entities.pet import Pet, PetSpecies, PetStatus
from src.shared.contracts.field_cipher import IFieldCipher
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
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AdoptionRequestRowMapper:
    """Descifra el correo y el teléfono del solicitante (solo los ve el admin)."""

    def __init__(self, cipher: IFieldCipher) -> None:
        self._cipher = cipher

    def to_entity(self, row: RowMapping) -> AdoptionRequest:
        phone = row["applicant_phone"]
        return AdoptionRequest(
            id=row["id"],
            status=AdoptionRequestStatus(row["status"]),
            pet_id=row["pet_id"],
            pet_name=row["pet_name"],
            pet_status=PetStatus(row["pet_status"]),
            applicant=Applicant(
                id=row["applicant_id"],
                name=row["applicant_name"],
                email=self._cipher.decrypt(row["applicant_email"], "users.email"),
                phone=self._cipher.decrypt(phone, "users.phone") if phone else None,
            ),
            reviewed_at=row["reviewed_at"],
            created_at=row["created_at"],
        )


def pet_to_dto(pet: Pet, storage: IImageStorage) -> PetAdminDto:
    return PetAdminDto(
        id=pet.id,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        age_years=pet.age_years,
        age_months=pet.age_months,
        image_url=storage.public_url(pet.image_url),
        status=pet.status,
        created_at=pet.created_at,
        updated_at=pet.updated_at,
    )


def adoption_request_to_dto(request: AdoptionRequest) -> AdoptionRequestAdminDto:
    return AdoptionRequestAdminDto(
        id=request.id,
        status=request.status,
        pet=AdoptionRequestPetDto(id=request.pet_id, name=request.pet_name, status=request.pet_status),
        applicant=ApplicantDto(
            id=request.applicant.id,
            name=request.applicant.name,
            email=request.applicant.email,
            phone=request.applicant.phone,
        ),
        reviewed_at=request.reviewed_at,
        created_at=request.created_at,
    )
