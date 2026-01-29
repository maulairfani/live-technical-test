import typing as t

from pydantic import BaseModel


class Content(BaseModel):
    item_id: str
    title: str
    content_type: t.Literal["series", "movie", "microdrama", "tv"]
    genre: str
    score: t.Optional[float] = None
