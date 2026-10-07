from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import get, put
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.targeting.errors import TargetingValidationError
from app.application.targeting.interactors.get_my_targeting import GetMyTargetingInteractor
from app.application.targeting.interactors.upsert_my_targeting import UpsertMyTargetingInteractor
from app.presentation.api.routes.targeting.dto import (
    TargetingResponse,
    UpsertTargetingRequest,
)


@get(
    path="/me",
    summary="Get own targeting rules",
    security=[{"BearerToken": []}],
)
async def get_targeting(
    interactor: FromDishka[GetMyTargetingInteractor],
) -> TargetingResponse:
    try:
        result = await interactor.execute()
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error
    r = result.rules
    return TargetingResponse(
        region=r.region,
        gender_target=r.gender_target,
        age_from=r.age_from,
        age_to=r.age_to,
    )


@put(
    path="/me",
    summary="Create or update own targeting rules",
    security=[{"BearerToken": []}],
)
async def upsert_targeting(
    data: UpsertTargetingRequest,
    interactor: FromDishka[UpsertMyTargetingInteractor],
) -> TargetingResponse:
    try:
        result = await interactor.execute(
            region=data.region,
            gender_target=data.gender_target,
            age_from=data.age_from,
            age_to=data.age_to,
        )
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error
    except TargetingValidationError as error:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid targeting rules (e.g. age_from >= 0, age_to >= age_from)",
        ) from error
    r = result.rules
    return TargetingResponse(
        region=r.region,
        gender_target=r.gender_target,
        age_from=r.age_from,
        age_to=r.age_to,
    )


router = DishkaRouter(
    path="/targeting",
    route_handlers=[get_targeting, upsert_targeting],
    tags=["targeting"],
)
