from pydantic_core import PydanticCustomError
from pydantic import BaseModel, EmailStr, Field, model_validator
from fastapi import Form
from typing_extensions import Self


class SUserCreate(BaseModel):
    email: EmailStr
    hashed_password: str


class SUserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class SUserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=5)
    confirmPassword: str

    @classmethod
    def as_form(
        cls,
        email: str = Form(...),
        password: str = Form(...),
        confirmPassword: str = Form(...)
    ) -> dict:
        return {
            "email": email,
            "password": password,
            "confirmPassword": confirmPassword
        }

    @model_validator(mode="after")
    def verify_password_match(self) -> Self:
        if self.password != self.confirmPassword:
            raise PydanticCustomError(
                "password_mismatch",
                "Passwords do not match. Please enter the same password."
            )
        return self


class SUserLogin(BaseModel):
    email: EmailStr
    password: str

    @classmethod
    def as_form(
        cls,
        email: str = Form(...),
        password: str = Form(...)
    ) -> dict:
        return {
            "email": email,
            "password": password
        }