from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.adoptions.user.data.mappers.adoption_user_mapper import row_to_my_request
from src.features.adoptions.user.data.models.adoption_user_tables import adoption_requests, pets
from src.features.adoptions.user.domain.entities.adoption_request import MyAdoptionRequest
from src.features.adoptions.user.domain.repositories.my_adoption_request_repository import (
    IMyAdoptionRequestRepository,
)
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.ids import new_id
from src.shared.utils.query import fetch_page
from src.shared.utils.time import utcnow


def _base_query():
    return (
        select(
            adoption_requests.c.id,
            adoption_requests.c.status,
            adoption_requests.c.pet_id,
            adoption_requests.c.created_at,
            pets.c.name.label("pet_name"),
            pets.c.species.label("pet_species"),
            pets.c.image_url.label("pet_image_url"),
        )
        .join(pets, pets.c.id == adoption_requests.c.pet_id)
        .where(adoption_requests.c.deleted_at.is_(None))
    )


class MyAdoptionRequestRepositoryImpl(IMyAdoptionRequestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_pending(self, user_id: str, pet_id: str) -> bool:
        query = select(
            exists().where(
                adoption_requests.c.user_id == user_id,
                adoption_requests.c.pet_id == pet_id,
                adoption_requests.c.status == "pending",
                adoption_requests.c.deleted_at.is_(None),
            )
        )
        return bool(await self._session.scalar(query))

    async def create(self, user_id: str, pet_id: str) -> MyAdoptionRequest:
        now = utcnow()
        request_id = new_id()
        await self._session.execute(
            adoption_requests.insert().values(
                id=request_id,
                pet_id=pet_id,
                user_id=user_id,
                status="pending",
                created_at=now,
                updated_at=now,
            )
        )
        await self._session.commit()
        row = (
            await self._session.execute(_base_query().where(adoption_requests.c.id == request_id))
        ).mappings().one()
        return row_to_my_request(row)

    async def list_by_user(self, user_id: str, page: PageRequest) -> Page[MyAdoptionRequest]:
        query = _base_query().where(adoption_requests.c.user_id == user_id)
        order = [adoption_requests.c.created_at.desc(), adoption_requests.c.id]
        return await fetch_page(self._session, query, order, page, row_to_my_request)
