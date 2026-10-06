from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.adoptions.user.data.mappers.adoption_user_mapper import row_to_pet
from src.features.adoptions.user.data.models.adoption_user_tables import pets
from src.features.adoptions.user.domain.entities.pet import Pet, PetFilters
from src.features.adoptions.user.domain.repositories.pet_catalog_repository import IPetCatalogRepository
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.query import fetch_page, order_by_whitelist
from src.shared.utils.sql import LIKE_ESCAPE, like_pattern

SORTABLE = {"created_at": pets.c.created_at, "name": pets.c.name}
PUBLIC_COLUMNS = (
    pets.c.id,
    pets.c.name,
    pets.c.species,
    pets.c.breed,
    pets.c.age_years,
    pets.c.age_months,
    pets.c.image_url,
    pets.c.status,
)


class PetCatalogRepositoryImpl(IPetCatalogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: PetFilters, page: PageRequest) -> Page[Pet]:
        query = select(*PUBLIC_COLUMNS).where(pets.c.deleted_at.is_(None))
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

    async def find_by_id(self, pet_id: str) -> Pet | None:
        query = select(*PUBLIC_COLUMNS).where(pets.c.id == pet_id, pets.c.deleted_at.is_(None))
        row = (await self._session.execute(query)).mappings().first()
        return row_to_pet(row) if row else None
