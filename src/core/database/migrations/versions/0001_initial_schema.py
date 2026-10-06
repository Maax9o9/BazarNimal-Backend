"""Esquema inicial de BazarNimal: usuarios, sesiones, adopciones, tienda y publicaciones.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# MySQL crea automáticamente un índice para cada llave foránea (con el nombre de la FK).
TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}

UNSIGNED_INT = sa.Integer().with_variant(mysql.INTEGER(unsigned=True), "mysql")
UNSIGNED_TINYINT = sa.SmallInteger().with_variant(mysql.TINYINT(unsigned=True), "mysql")


def _id() -> sa.Column:
    return sa.Column("id", sa.CHAR(36), primary_key=True)


def _audit_columns(soft_delete: bool = True) -> list[sa.Column]:
    is_mysql = op.get_context().dialect.name == "mysql"
    on_update = " ON UPDATE CURRENT_TIMESTAMP" if is_mysql else ""
    columns = [
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text(f"CURRENT_TIMESTAMP{on_update}"),
        ),
    ]
    if soft_delete:
        columns.append(sa.Column("deleted_at", sa.DateTime(), nullable=True))
    return columns


def upgrade() -> None:
    op.create_table(
        "users",
        _id(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email_encrypted", sa.String(512), nullable=False),
        sa.Column("email_hash", sa.CHAR(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("phone_encrypted", sa.String(512), nullable=True),
        sa.Column("role", sa.Enum("user", "admin", name="user_role"), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failed_login_attempts", UNSIGNED_INT, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        *_audit_columns(),
        sa.UniqueConstraint("email_hash", name="uq_users_email_hash"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "refresh_tokens",
        _id(),
        sa.Column("user_id", sa.CHAR(36), nullable=False),
        sa.Column("token_hash", sa.CHAR(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("replaced_by", sa.CHAR(36), nullable=True),
        sa.Column("created_by_ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_refresh_tokens_user", ondelete="CASCADE", onupdate="CASCADE"
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.create_table(
        "pets",
        _id(),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("species", sa.Enum("dog", "cat", name="pet_species"), nullable=False),
        sa.Column("breed", sa.String(80), nullable=False),
        sa.Column("age_years", UNSIGNED_TINYINT, nullable=False, server_default="0"),
        sa.Column("age_months", UNSIGNED_TINYINT, nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("in_adoption", "adopted", name="pet_status"),
            nullable=False,
            server_default="in_adoption",
        ),
        sa.Column("created_by", sa.CHAR(36), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_pets_created_by", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_pets_listing", "pets", ["deleted_at", "status", "species"])
    op.create_index("ix_pets_name", "pets", ["name"])

    op.create_table(
        "adoption_requests",
        _id(),
        sa.Column("pet_id", sa.CHAR(36), nullable=False),
        sa.Column("user_id", sa.CHAR(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="adoption_request_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_by", sa.CHAR(36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["pet_id"], ["pets.id"], name="fk_adoption_requests_pet", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_adoption_requests_user", ondelete="CASCADE", onupdate="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            name="fk_adoption_requests_reviewed_by",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_adoption_requests_status", "adoption_requests", ["deleted_at", "status"])

    op.create_table(
        "products",
        _id(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("image_url", sa.String(255), nullable=False),
        sa.Column("weight_kg", sa.Numeric(8, 3), nullable=True),
        sa.Column("pieces", UNSIGNED_INT, nullable=True),
        sa.Column(
            "status",
            sa.Enum("available", "unavailable", name="product_status"),
            nullable=False,
            server_default="available",
        ),
        sa.Column("created_by", sa.CHAR(36), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_products_created_by", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_products_listing", "products", ["deleted_at", "status"])
    op.create_index("ix_products_name", "products", ["name"])

    op.create_table(
        "posts",
        _id(),
        sa.Column("user_id", sa.CHAR(36), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="post_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_by", sa.CHAR(36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_posts_user", ondelete="CASCADE", onupdate="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"], ["users.id"], name="fk_posts_reviewed_by", ondelete="SET NULL", onupdate="CASCADE"
        ),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_posts_listing", "posts", ["deleted_at", "status", "created_at"])


def downgrade() -> None:
    op.drop_table("posts")
    op.drop_table("products")
    op.drop_table("adoption_requests")
    op.drop_table("pets")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
