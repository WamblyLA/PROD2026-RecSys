from pydantic import BaseModel, Field


class UpsertTargetingRequest(BaseModel):
    region: str | None = Field(None, min_length=1, max_length=120)
    gender_target: str = Field(..., pattern="^(male|female|both)$")
    age_from: int = Field(..., ge=0)
    age_to: int = Field(..., ge=0)


class TargetingResponse(BaseModel):
    region: str | None
    gender_target: str
    age_from: int
    age_to: int
