"""Pydantic schemas for the auth module - shapes of register/login requests and responses."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """What the client must send to create a new account."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """What the client must send to log in."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """What we send back after a successful login - the client stores this and sends it on future requests."""

    access_token: str
    token_type: str = "bearer"
