from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors.exceptions import ConflictError
from src.features.adoptions.admin.data.mappers.adoption_admin_mapper import AdoptionRequestRowMapper
from src.features.adoptions.admin.data.models.adoption_tables import adoption_requests, pets, users
from src.features.adoptions.admin.domain.entities.adoption_request import AdoptionRequest, AdoptionRequestFilters
from src.features.adoptions.admin.domain.repositories.adoption_request_repository import IAdoptionRequestRepository
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.query import fetch_page
from src.shared.utils.time import utcnow


def _base_query() -> Select:
    return (
        select(
            adoption_requests.c.id,
            adoption_requests.c.status,
            adoption_requests.c.pet_id,
            adoption_requests.c.reviewed_at,
            adoption_requests.c.created_at,
            pets.c.name.label("pet_name"),
            pets.c.status.label("pet_status"),
            users.c.id.label("applicant_id"),
            users.c.name.label("applicant_name"),
            users.c.email_encrypted.label("applicant_email"),
            users.c.phone_encrypted.label("applicant_phone"),
        )
        .join(pets, pets.c.id == adoption_requests.c.pet_id)
        .join(users, users.c.id == adoption_requests.c.user_id)
        .where(adoption_requests.c.deleted_at.is_(None))
    )


class AdoptionRequestRepositoryImpl(IAdoptionRequestRepository):
    def __init__(self, session: AsyncSession, mapper: AdoptionRequestRowMapper) -> None:
        self._session = session
        self._mapper = mapper

    async def list(self, filters: AdoptionRequestFilters, page: PageRequest) -> Page[AdoptionRequest]:
        query = _base_query()
        if filters.status:
            query = query.where(adoption_requests.c.status == filters.status.value)
        if filters.pet_id:
            query = query.where(adoption_requests.c.pet_id == filters.pet_id)
        order = [adoption_requests.c.created_at.desc(), adoption_requests.c.id]
        return await fetch_page(self._session, query, order, page, self._mapper.to_entity)

    async def find_by_id(self, request_id: str) -> AdoptionRequest | None:
        row = (
            await self._session.execute(_base_query().where(adoption_requests.c.id == request_id))
        ).mappings().first()
        return self._mapper.to_entity(row) if row else None

    async def approve(self, request_id: str, pet_id: str, reviewer_id: str) -> None:
        now = utcnow()
        try:
            # Actualizaciones condicionales: si otro admin se adelantó, no se modifica nada.
            pet_result = await self._session.execute(
                update(pets)
                .where(pets.c.id == pet_id, pets.c.status == "in_adoption", pets.c.deleted_at.is_(None))
                .values(status="adopted", updated_at=now)
            )
            request_result = await self._session.execute(
                update(adoption_requests)
                .where(adoption_requests.c.id == request_id, adoption_requests.c.status == "pending")
                .values(status="approved", reviewed_by=reviewer_id, reviewed_at=now, updated_at=now)
            )
            if pet_result.rowcount != 1 or request_result.rowcount != 1:
                await self._session.rollback()
                raise ConflictError("La solicitud o la mascota cambiaron de estado. Recarga e intenta de nuevo.")
            await self._session.execute(
                update(adoption_requests)
                .where(
                    adoption_requests.c.pet_id == pet_id,
                    adoption_requests.c.id != request_id,
                    adoption_requests.c.status == "pending",
                )
                .values(status="rejected", reviewed_by=reviewer_id, reviewed_at=now, updated_at=now)
            )
            await self._session.commit()
        except ConflictError:
            raise
        except Exception:
            await self._session.rollback()
            raise

    async def reject(self, request_id: str, reviewer_id: str) -> None:
        now = utcnow()
        result = await self._session.execute(
            update(adoption_requests)
            .where(adoption_requests.c.id == request_id, adoption_requests.c.status == "pending")
            .values(status="rejected", reviewed_by=reviewer_id, reviewed_at=now, updated_at=now)
        )
        if result.rowcount != 1:
            await self._session.rollback()
            raise ConflictError("La solicitud ya fue revisada")
        await self._session.commit()
