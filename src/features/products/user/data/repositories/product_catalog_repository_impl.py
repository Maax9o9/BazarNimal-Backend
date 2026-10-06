from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.products.user.data.mappers.product_mapper import row_to_product
from src.features.products.user.data.models.product_catalog_tables import products
from src.features.products.user.domain.entities.product import Product, ProductFilters
from src.features.products.user.domain.repositories.product_catalog_repository import IProductCatalogRepository
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.query import fetch_page, order_by_whitelist
from src.shared.utils.sql import LIKE_ESCAPE, like_pattern

SORTABLE = {"created_at": products.c.created_at, "name": products.c.name}
PUBLIC_COLUMNS = (
    products.c.id,
    products.c.name,
    products.c.image_url,
    products.c.weight_kg,
    products.c.pieces,
    products.c.status,
)


class ProductCatalogRepositoryImpl(IProductCatalogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: ProductFilters, page: PageRequest) -> Page[Product]:
        query = select(*PUBLIC_COLUMNS).where(products.c.deleted_at.is_(None))
        if filters.status:
            query = query.where(products.c.status == filters.status.value)
        if filters.search:
            query = query.where(products.c.name.like(like_pattern(filters.search), escape=LIKE_ESCAPE))
        order = order_by_whitelist(filters.sort, SORTABLE, "name")
        return await fetch_page(self._session, query, [order, products.c.id], page, row_to_product)

    async def find_by_id(self, product_id: str) -> Product | None:
        query = select(*PUBLIC_COLUMNS).where(products.c.id == product_id, products.c.deleted_at.is_(None))
        row = (await self._session.execute(query)).mappings().first()
        return row_to_product(row) if row else None
