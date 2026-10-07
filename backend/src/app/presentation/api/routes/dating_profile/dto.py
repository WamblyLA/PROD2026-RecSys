from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


class UpsertDatingProfileRequest(BaseModel):
    photos: list[Annotated[str, Field(max_length=2048)]] = Field(..., min_length=1)


class TraitItemResponse(BaseModel):
    trait_code: str
    score: float
    is_hidden: bool


class DatingProfileResponse(BaseModel):
    user_id: UUID
    photos: list[str]
    traits: list[TraitItemResponse]


class SetTraitVisibilityRequest(BaseModel):
    trait_code: str = Field(..., min_length=1, max_length=64)
    is_hidden: bool = Field(...)


class UploadDatingPhotoResponse(BaseModel):
    photo_url: str
