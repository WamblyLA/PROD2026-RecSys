from pydantic import BaseModel, EmailStr, Field


class EmailSignUpRequest(BaseModel):
    email: EmailStr = Field(..., max_length=320)
    password: str = Field(..., min_length=8)


class EmailSignInRequest(BaseModel):
    email: EmailStr = Field(..., max_length=320)
    password: str = Field(..., min_length=1)


class YandexSignUpRequest(BaseModel):
    code: str = Field(..., min_length=1)


class YandexSignInRequest(BaseModel):
    code: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    user_id: str
    access_token: str
