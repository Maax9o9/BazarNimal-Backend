import sqlalchemy as sa

metadata = sa.MetaData()

pets = sa.Table(
    "pets",
    metadata,
    sa.Column("id", sa.CHAR(36), primary_key=True),
    sa.Column("name", sa.String(80)),
    sa.Column("species", sa.String(10)),
    sa.Column("breed", sa.String(80)),
    sa.Column("age_years", sa.SmallInteger),
    sa.Column("age_months", sa.SmallInteger),
    sa.Column("image_url", sa.String(255)),
    sa.Column("status", sa.String(20)),
    sa.Column("created_by", sa.CHAR(36)),
    sa.Column("created_at", sa.DateTime),
    sa.Column("updated_at", sa.DateTime),
    sa.Column("deleted_at", sa.DateTime),
)

adoption_requests = sa.Table(
    "adoption_requests",
    metadata,
    sa.Column("id", sa.CHAR(36), primary_key=True),
    sa.Column("pet_id", sa.CHAR(36)),
    sa.Column("user_id", sa.CHAR(36)),
    sa.Column("status", sa.String(10)),
    sa.Column("reviewed_by", sa.CHAR(36)),
    sa.Column("reviewed_at", sa.DateTime),
    sa.Column("created_at", sa.DateTime),
    sa.Column("updated_at", sa.DateTime),
    sa.Column("deleted_at", sa.DateTime),
)

# Solo los campos de contacto del solicitante.
users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.CHAR(36), primary_key=True),
    sa.Column("name", sa.String(100)),
    sa.Column("email_encrypted", sa.String(512)),
    sa.Column("phone_encrypted", sa.String(512)),
)
