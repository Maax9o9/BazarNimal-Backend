from pydantic import BaseModel, Field

from src.shared.types.roles import Role


class UserDto(BaseModel):
    id: str
    name: str
    email: str
    phone: str | None
    role: Role


class SessionDto(BaseModel):
    user: UserDto
    role: Role = Field(description="Úsalo en el frontend para redirigir a la vista de user o admin")
    expires_in: int = Field(description="Segundos de vida del access token (15 min user, 2 h admin)")
