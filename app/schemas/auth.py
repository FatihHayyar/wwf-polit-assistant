from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr


class RegisterResponse(BaseModel):
    message: str


class VerifyEmailResponse(BaseModel):
    message: str