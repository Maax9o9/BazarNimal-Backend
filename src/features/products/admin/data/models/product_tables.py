import sqlalchemy as sa

metadata = sa.MetaData()

products = sa.Table(
    "products",
    metadata,
    sa.Column("id", sa.CHAR(36), primary_key=True),
    sa.Column("name", sa.String(120)),
    sa.Column("image_url", sa.String(255)),
    sa.Column("weight_kg", sa.Numeric(8, 3)),
    sa.Column("pieces", sa.Integer),
    sa.Column("status", sa.String(15)),
    sa.Column("created_by", sa.CHAR(36)),
    sa.Column("created_at", sa.DateTime),
    sa.Column("updated_at", sa.DateTime),
    sa.Column("deleted_at", sa.DateTime),
)
