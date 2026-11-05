from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr


class RegisterResponse(BaseModel):
    message: str
    # "verification_link" or "login_link": which email was sent.
    result: str


class VerifyEmailResponse(BaseModel):
    message: str