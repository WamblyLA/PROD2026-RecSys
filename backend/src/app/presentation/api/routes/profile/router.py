from uuid import UUID

from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import get, put
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.profile.errors import CardUserNotFoundError, ProfileNotFoundError
from app.application.profile.interactors.get_profile import GetProfileInteractor
from app.application.profile.interactors.get_self_card import GetSelfCardInteractor
from app.application.profile.interactors.get_user_card import GetUserCardInteractor
from app.application.profile.interactors.upsert_profile import UpsertProfileInteractor
from app.domain.user.entity import UserId
from app.presentation.api.routes.profile.dto import (
    CardDatingProfileResponse,
    CardDatingTraitResponse,
    ProfileResponse,
    SelfCardResponse,
    UpsertProfileRequest,
)


@get(
    path="/",
    summary="Get own profile",
    security=[{"BearerToken": []}],
)
async def get_profile(
    interactor: FromDishka[GetProfileInteractor],
) -> ProfileResponse:
    try:
        result = await interactor.execute()
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Profile not set yet") from error

    p = result.profile
    return ProfileResponse(
        user_id=result.user_id,
        first_name=p.first_name,
        last_name=p.last_name,
        birth_date=p.birth_date,
        gender=p.gender,
        region=p.region,
        avatar_url=p.avatar_url,
    )


@put(
    path="/",
    summary="Create or update own profile",
    security=[{"BearerToken": []}],
)
async def upsert_profile(
    data: UpsertProfileRequest,
    interactor: FromDishka[UpsertProfileInteractor],
) -> ProfileResponse:
    try:
        result = await interactor.execute(
            first_name=data.first_name,
            last_name=data.last_name,
            birth_date=data.birth_date,
            gender=data.gender,
            region=data.region,
            avatar_url=data.avatar_url,
        )
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error

    p = result.profile
    return ProfileResponse(
        user_id=result.user_id,
        first_name=p.first_name,
        last_name=p.last_name,
        birth_date=p.birth_date,
        gender=p.gender,
        region=p.region,
        avatar_url=p.avatar_url,
    )


@get(
    path="/card",
    summary="Get own card",
    security=[{"BearerToken": []}],
)
async def get_self_card(
    interactor: FromDishka[GetSelfCardInteractor],
) -> SelfCardResponse:
    try:
        result = await interactor.execute()
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error

    profile_response: ProfileResponse | None = None
    if result.profile is not None:
        profile_response = ProfileResponse(
            user_id=result.user_id,
            first_name=result.profile.first_name,
            last_name=result.profile.last_name,
            birth_date=result.profile.birth_date,
            gender=result.profile.gender,
            region=result.profile.region,
            avatar_url=result.profile.avatar_url,
        )

    dating_profile_response: CardDatingProfileResponse | None = None
    if result.dating_profile is not None:
        dating_profile_response = CardDatingProfileResponse(
            photos=result.dating_profile.photos,
            traits=[
                CardDatingTraitResponse(
                    trait_code=trait.trait_code,
                    score=trait.score,
                    is_hidden=trait.is_hidden,
                )
                for trait in result.dating_profile.traits
            ],
        )

    return SelfCardResponse(
        user_id=result.user_id,
        profile=profile_response,
        dating_profile=dating_profile_response,
    )


@get(
    path="/card/{user_id:uuid}",
    summary="Get user card by user id",
    security=[{"BearerToken": []}],
)
async def get_user_card(
    user_id: UUID,
    interactor: FromDishka[GetUserCardInteractor],
) -> SelfCardResponse:
    try:
        result = await interactor.execute(user_id=UserId(user_id))
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error
    except CardUserNotFoundError as error:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found") from error

    profile_response: ProfileResponse | None = None
    if result.profile is not None:
        profile_response = ProfileResponse(
            user_id=result.user_id,
            first_name=result.profile.first_name,
            last_name=result.profile.last_name,
            birth_date=result.profile.birth_date,
            gender=result.profile.gender,
            region=result.profile.region,
            avatar_url=result.profile.avatar_url,
        )

    dating_profile_response: CardDatingProfileResponse | None = None
    if result.dating_profile is not None:
        dating_profile_response = CardDatingProfileResponse(
            photos=result.dating_profile.photos,
            traits=[
                CardDatingTraitResponse(
                    trait_code=trait.trait_code,
                    score=trait.score,
                    is_hidden=trait.is_hidden,
                )
                for trait in result.dating_profile.traits
            ],
        )

    return SelfCardResponse(
        user_id=result.user_id,
        profile=profile_response,
        dating_profile=dating_profile_response,
    )


router = DishkaRouter(
    path="/profile",
    route_handlers=[get_profile, get_self_card, get_user_card, upsert_profile],
    tags=["profile"],
)
