import typing as t
from datetime import datetime

from pydantic import BaseModel

from src.schemas.content import Content


class GlobalRecommendationRequest(BaseModel):
    top_k: int = 10

    # Optionals
    date: t.Optional[datetime] = None
    content_types: t.List[t.Literal["series", "movie", "microdrama", "tv"]] = [
        "series",
        "movie",
        "microdrama",
        "tv",
    ]
    lookback_days: int = 30
    gravity: float = 1.5


class GlobalRecommendationResponse(BaseModel):
    top_k: int
    items: t.List[Content]
