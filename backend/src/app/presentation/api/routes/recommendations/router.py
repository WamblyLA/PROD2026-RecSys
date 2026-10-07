from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import get
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_503_SERVICE_UNAVAILABLE

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.profile.errors import ProfileNotFoundError
from app.application.recommendation.errors import (
    RecommendationCandidatesNotFoundError,
    RecommendationProviderUnavailableError,
)
from app.application.recommendation.interactors.get_recommendations import GetRecommendationsInteractor
from app.presentation.api.routes.recommendations.dto import RecommendationsResponse


@get(
    path="/",
    summary="Get personalized candidates for current user",
    security=[{"BearerToken": []}],
)
async def get_recommendations(
    interactor: FromDishka[GetRecommendationsInteractor],
) -> RecommendationsResponse:
    try:
        result = await interactor.execute()
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Profile not set yet") from error
    except RecommendationCandidatesNotFoundError as error:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except RecommendationProviderUnavailableError as error:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error

    return RecommendationsResponse(
        items=[
            {
                "ml_recommendation_id": item.ml_recommendation_id,
                "user_id": item.user_id,
                "candidate_user_id": item.candidate_user_id,
                "reasons": item.reasons,
                "candidate_card": (
                    {
                        "user_id": item.candidate_card.user_id,
                        "profile": (
                            {
                                "first_name": item.candidate_card.profile.first_name,
                                "last_name": item.candidate_card.profile.last_name,
                                "birth_date": item.candidate_card.profile.birth_date,
                                "gender": item.candidate_card.profile.gender,
                                "region": item.candidate_card.profile.region,
                                "avatar_url": item.candidate_card.profile.avatar_url,
                            }
                            if item.candidate_card.profile is not None
                            else None
                        ),
                        "dating_profile": (
                            {
                                "photos": item.candidate_card.dating_profile.photos,
                                "traits": [
                                    {
                                        "trait_code": trait.trait_code,
                                        "score": trait.score,
                                        "is_hidden": trait.is_hidden,
                                    }
                                    for trait in item.candidate_card.dating_profile.traits
                                ],
                            }
                            if item.candidate_card.dating_profile is not None
                            else None
                        ),
                    }
                    if item.candidate_card is not None
                    else None
                ),
            }
            for item in result.items
        ],
    )


router = DishkaRouter(
    path="/recommendations",
    route_handlers=[get_recommendations],
    tags=["recommendations"],
)
