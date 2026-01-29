from fastapi import APIRouter

from src.services.global_recommendation_service import (
    GlobalRecommendationRequest,
    GlobalRecommendationService,
)
from src.services.personal_recommendation_service import (
    PersonalRecommendationRequest,
    PersonalRecommendationService,
)

router = APIRouter(prefix="/v1", tags=["recommendation"])


@router.post("/popular")
def recommend_popular(req: GlobalRecommendationRequest):
    """Get popular content recommendations."""
    service = GlobalRecommendationService()
    return service.recommend_popular(req)


@router.post("/recommendations")
def recommend_for_user(req: PersonalRecommendationRequest):
    """Get personalized recommendations for a user."""
    service = PersonalRecommendationService()
    return service.recommend_for_user(req)
