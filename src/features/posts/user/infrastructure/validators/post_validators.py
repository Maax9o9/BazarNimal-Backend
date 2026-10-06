from typing import Annotated

from pydantic import Field, StringConstraints

from src.shared.validators.common import StrictSchema
from src.shared.validators.image import ImageUpload

PostContent = Annotated[str, StringConstraints(min_length=1, max_length=1000)]


class CreatePostForm(StrictSchema):
    content: PostContent = Field(description="Texto de la publicación (máximo 1000 caracteres)")
    image: ImageUpload = Field(description="Imagen de la publicación (JPEG, PNG o WEBP)")
