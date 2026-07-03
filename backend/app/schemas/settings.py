from pydantic import BaseModel, Field


class CacheThresholdUpdateRequest(BaseModel):
    similarity_threshold: float = Field(ge=0.0, le=1.0)


class CacheThresholdUpdateResponse(BaseModel):
    similarity_threshold: float
    message: str
