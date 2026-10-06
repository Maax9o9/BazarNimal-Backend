import sqlalchemy as sa

metadata = sa.MetaData()

posts = sa.Table(
    "posts",
    metadata,
    sa.Column("id", sa.CHAR(36), primary_key=True),
    sa.Column("user_id", sa.CHAR(36)),
    sa.Column("content", sa.Text),
    sa.Column("image_url", sa.String(255)),
    sa.Column("status", sa.String(10)),
    sa.Column("created_at", sa.DateTime),
    sa.Column("updated_at", sa.DateTime),
    sa.Column("deleted_at", sa.DateTime),
)

# Solo el nombre del autor: nunca se exponen sus datos de contacto en publicaciones.
users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.CHAR(36), primary_key=True),
    sa.Column("name", sa.String(100)),
)
