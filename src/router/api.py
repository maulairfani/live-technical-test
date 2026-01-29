from fastapi import APIRouter

from .v1 import recommendation

router = APIRouter()
router.include_router(recommendation.router)
