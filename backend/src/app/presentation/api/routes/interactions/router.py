from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import post
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.interaction.errors import (
    CandidateNotFoundError,
    CandidateNotRecommendedError,
    SelfInteractionError,
)
from app.application.interaction.interactors.create_interaction import CreateInteractionInteractor
from app.domain.interaction.value_objects import InteractionType
from app.domain.user.entity import UserId
from app.presentation.api.routes.interactions.dto import CreateInteractionRequest, InteractionResponse


@post(
    path="/",
    summary="Append interaction event for candidate",
    status_code=201,
    security=[{"BearerToken": []}],
)
async def create_interaction(
    data: CreateInteractionRequest,
    interactor: FromDishka[CreateInteractionInteractor],
) -> InteractionResponse:
    try:
        result = await interactor.execute(
            candidate_user_id=UserId(data.candidate_user_id),
            action=InteractionType(data.action),
            ml_recommendation_id=data.ml_recommendation_id,
        )
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error
    except SelfInteractionError as error:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Cannot interact with yourself",
        ) from error
    except CandidateNotFoundError as error:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        ) from error
    except CandidateNotRecommendedError as error:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Candidate was not recommended for current user",
        ) from error

    return InteractionResponse(
        interaction_id=result.interaction_id,
        actor_user_id=result.actor_user_id,
        candidate_user_id=result.candidate_user_id,
        action=result.action.value,
        created_at=result.created_at,
        ml_recommendation_id=result.ml_recommendation_id,
    )


router = DishkaRouter(
    path="/interactions",
    route_handlers=[create_interaction],
    tags=["interactions"],
)
