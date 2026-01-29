import typing as t

from pydantic import BaseModel

from src.schemas.content import Content


class PersonalRecommendationRequest(BaseModel):
    user_id: str
    top_k: int = 10

    # Optionals
    content_types: t.List[t.Literal["series", "movie", "microdrama", "tv"]] = [
        "series",
        "movie",
        "microdrama",
        "tv",
    ]
    top_p: int = 10


class PersonalRecommendationResponse(BaseModel):
    user_id: str
    top_k: int
    items: t.List[Content]
    fallback_used: bool
