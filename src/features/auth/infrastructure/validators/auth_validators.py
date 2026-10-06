from typing import Annotated

from pydantic import EmailStr, Field, StringConstraints

from src.shared.validators.common import PersonName, PhoneNumber, StrictSchema, StrongPassword

Email = Annotated[EmailStr, StringConstraints(max_length=254)]


class RegisterRequest(StrictSchema):
    name: PersonName = Field(examples=["María López"])
    email: Email = Field(examples=["maria@example.com"])
    phone: PhoneNumber = Field(examples=["5512345678"])
    password: StrongPassword = Field(examples=["Catrina#2026"])


class LoginRequest(StrictSchema):
    email: Email
    password: str = Field(min_length=1, max_length=128)
