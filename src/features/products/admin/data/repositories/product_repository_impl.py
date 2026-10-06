from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors.exceptions import NotFoundError
from src.features.products.admin.data.mappers.product_admin_mapper import row_to_product
from src.features.products.admin.data.models.product_tables import products
from src.features.products.admin.domain.entities.product import Product, ProductData, ProductFilters
from src.features.products.admin.domain.repositories.product_repository import IProductRepository
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.ids import new_id
from src.shared.utils.query import fetch_page, order_by_whitelist
from src.shared.utils.sql import LIKE_ESCAPE, like_pattern
from src.shared.utils.time import utcnow

SORTABLE = {"created_at": products.c.created_at, "name": products.c.name}


class ProductRepositoryImpl(IProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ProductData, image_url: str, created_by: str) -> Product:
        now = utcnow()
        product_id = new_id()
        await self._session.execute(
            products.insert().values(
                id=product_id,
                **self._columns(data),
                image_url=image_url,
                created_by=created_by,
                created_at=now,
                updated_at=now,
            )
        )
        await self._session.commit()
        return await self._get(product_id)

    async def find_by_id(self, product_id: str) -> Product | None:
        query = select(products).where(products.c.id == product_id, products.c.deleted_at.is_(None))
        row = (await self._session.execute(query)).mappings().first()
        return row_to_product(row) if row else None

    async def list(self, filters: ProductFilters, page: PageRequest) -> Page[Product]:
        query = select(products).where(products.c.deleted_at.is_(None))
        if filters.status:
            query = query.where(products.c.status == filters.status.value)
        if filters.search:
            query = query.where(products.c.name.like(like_pattern(filters.search), escape=LIKE_ESCAPE))
        order = order_by_whitelist(filters.sort, SORTABLE, "-created_at")
        return await fetch_page(self._session, query, [order, products.c.id], page, row_to_product)

    async def update(self, product_id: str, data: ProductData, image_url: str) -> Product:
        await self._session.execute(
            update(products)
            .where(products.c.id == product_id, products.c.deleted_at.is_(None))
            .values(**self._columns(data), image_url=image_url, updated_at=utcnow())
        )
        await self._session.commit()
        return await self._get(product_id)

    async def soft_delete(self, product_id: str) -> None:
        now = utcnow()
        await self._session.execute(
            update(products).where(products.c.id == product_id).values(deleted_at=now, updated_at=now)
        )
        await self._session.commit()

    async def _get(self, product_id: str) -> Product:
        product = await self.find_by_id(product_id)
        if product is None:
            raise NotFoundError("El artículo no existe")
        return product

    @staticmethod
    def _columns(data: ProductData) -> dict[str, object]:
        return {
            "name": data.name,
            "weight_kg": data.weight_kg,
            "pieces": data.pieces,
            "status": data.status.value,
        }
