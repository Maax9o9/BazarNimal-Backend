"""Paginación de consultas SQLAlchemy Core (siempre parametrizadas)."""

from collections.abc import Callable, Mapping
from typing import Any

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.types.pagination import Page, PageRequest


def order_by_whitelist(sort: str | None, allowed: Mapping[str, ColumnElement[Any]], default: str) -> ColumnElement[Any]:
    """`ORDER BY` no se puede parametrizar: solo se aceptan columnas de una lista blanca."""
    key = sort if sort and sort.lstrip("-") in allowed else default
    column = allowed[key.lstrip("-")]
    return column.desc() if key.startswith("-") else column.asc()


async def fetch_page[T](
    session: AsyncSession,
    query: Select[Any],
    order_by: list[ColumnElement[Any]],
    page: PageRequest,
    to_entity: Callable[[RowMapping], T],
) -> Page[T]:
    total = await session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    rows = (
        await session.execute(query.order_by(*order_by).limit(page.limit).offset(page.offset))
    ).mappings().all()
    return Page(items=[to_entity(row) for row in rows], total=int(total or 0), page=page.page, limit=page.limit)
