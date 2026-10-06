"""Esquema de las tablas que usa la feature auth (SQLAlchemy Core: consultas siempre parametrizadas)."""

import sqlalchemy as sa

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.CHAR(36), primary_key=True),
    sa.Column("name", sa.String(100)),
    sa.Column("email_encrypted", sa.String(512)),
    sa.Column("email_hash", sa.CHAR(64)),
    sa.Column("password_hash", sa.String(255)),
    sa.Column("phone_encrypted", sa.String(512)),
    sa.Column("role", sa.String(10)),
    sa.Column("is_active", sa.Boolean),
    sa.Column("failed_login_attempts", sa.Integer),
    sa.Column("locked_until", sa.DateTime),
    sa.Column("created_at", sa.DateTime),
    sa.Column("updated_at", sa.DateTime),
    sa.Column("deleted_at", sa.DateTime),
)

refresh_tokens = sa.Table(
    "refresh_tokens",
    metadata,
    sa.Column("id", sa.CHAR(36), primary_key=True),
    sa.Column("user_id", sa.CHAR(36)),
    sa.Column("token_hash", sa.CHAR(64)),
    sa.Column("expires_at", sa.DateTime),
    sa.Column("revoked_at", sa.DateTime),
    sa.Column("replaced_by", sa.CHAR(36)),
    sa.Column("created_by_ip", sa.String(45)),
    sa.Column("user_agent", sa.String(255)),
    sa.Column("created_at", sa.DateTime),
)
