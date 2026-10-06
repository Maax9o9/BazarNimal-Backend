from decimal import Decimal

from sqlalchemy import RowMapping

from src.features.products.admin.data.dtos.product_admin_dtos import ProductAdminDto
from src.features.products.admin.domain.entities.product import Product, ProductStatus
from src.shared.contracts.image_storage import IImageStorage


def row_to_product(row: RowMapping) -> Product:
    weight = row["weight_kg"]
    pieces = row["pieces"]
    return Product(
        id=row["id"],
        name=row["name"],
        image_url=row["image_url"],
        weight_kg=Decimal(str(weight)) if weight is not None else None,
        pieces=int(pieces) if pieces is not None else None,
        status=ProductStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def product_to_dto(product: Product, storage: IImageStorage) -> ProductAdminDto:
    return ProductAdminDto(
        id=product.id,
        name=product.name,
        image_url=storage.public_url(product.image_url),
        weight_kg=product.weight_kg,
        pieces=product.pieces,
        status=product.status,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
