from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors.exceptions import NotFoundError
from src.features.adoptions.admin.data.mappers.adoption_admin_mapper import row_to_pet
from src.features.adoptions.admin.data.models.adoption_tables import adoption_requests, pets
from src.features.adoptions.admin.domain.entities.pet import Pet, PetData, PetFilters
from src.features.adoptions.admin.domain.repositories.pet_repository import IPetRepository
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.ids import new_id
from src.shared.utils.query import fetch_page, order_by_whitelist
from src.shared.utils.sql import LIKE_ESCAPE, like_pattern
from src.shared.utils.time import utcnow

SORTABLE = {"created_at": pets.c.created_at, "name": pets.c.name}


class PetRepositoryImpl(IPetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: PetData, image_url: str, created_by: str) -> Pet:
        now = utcnow()
        pet_id = new_id()
        await self._session.execute(
            pets.insert().values(
                id=pet_id,
                **self._columns(data),
                image_url=image_url,
                created_by=created_by,
                created_at=now,
                updated_at=now,
            )
        )
        await self._session.commit()
        return await self._get(pet_id)

    async def find_by_id(self, pet_id: str) -> Pet | None:
        row = (
            await self._session.execute(select(pets).where(pets.c.id == pet_id, pets.c.deleted_at.is_(None)))
        ).mappings().first()
        return row_to_pet(row) if row else None

    async def list(self, filters: PetFilters, page: PageRequest) -> Page[Pet]:
        query = select(pets).where(pets.c.deleted_at.is_(None))
        if filters.species:
            query = query.where(pets.c.species == filters.species.value)
        if filters.status:
            query = query.where(pets.c.status == filters.status.value)
        if filters.search:
            pattern = like_pattern(filters.search)
            query = query.where(
                pets.c.name.like(pattern, escape=LIKE_ESCAPE) | pets.c.breed.like(pattern, escape=LIKE_ESCAPE)
            )
        order = order_by_whitelist(filters.sort, SORTABLE, "-created_at")
        return await fetch_page(self._session, query, [order, pets.c.id], page, row_to_pet)

    async def update(self, pet_id: str, data: PetData, image_url: str) -> Pet:
        await self._session.execute(
            update(pets)
            .where(pets.c.id == pet_id, pets.c.deleted_at.is_(None))
            .values(**self._columns(data), image_url=image_url, updated_at=utcnow())
        )
        await self._session.commit()
        return await self._get(pet_id)

    async def soft_delete(self, pet_id: str) -> None:
        now = utcnow()
        try:
            await self._session.execute(
                update(pets).where(pets.c.id == pet_id).values(deleted_at=now, updated_at=now)
            )
            await self._session.execute(
                update(adoption_requests)
                .where(
                    adoption_requests.c.pet_id == pet_id,
                    adoption_requests.c.status == "pending",
                    adoption_requests.c.deleted_at.is_(None),
                )
                .values(status="rejected", reviewed_at=now, updated_at=now)
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def _get(self, pet_id: str) -> Pet:
        pet = await self.find_by_id(pet_id)
        if pet is None:
            raise NotFoundError("La mascota no existe")
        return pet

    @staticmethod
    def _columns(data: PetData) -> dict[str, object]:
        return {
            "name": data.name,
            "species": data.species.value,
            "breed": data.breed,
            "age_years": data.age_years,
            "age_months": data.age_months,
            "status": data.status.value,
        }
