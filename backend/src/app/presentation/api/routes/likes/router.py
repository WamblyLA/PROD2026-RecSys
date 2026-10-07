from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import get
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_401_UNAUTHORIZED

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.incoming_likes.interactors.get_my_incoming_likes import (
    GetMyIncomingLikesInteractor,
)
from app.presentation.api.routes.likes.dto import (
    IncomingLikeCandidateCardResponse,
    IncomingLikeCandidateDatingProfileResponse,
    IncomingLikeCandidateDatingTraitResponse,
    IncomingLikeCandidateProfileResponse,
    IncomingLikeItemResponse,
    IncomingLikesResponse,
)


@get(
    path="/incoming/me",
    summary="Get users who liked me and await my reply",
    security=[{"BearerToken": []}],
)
async def get_my_incoming_likes(
    interactor: FromDishka[GetMyIncomingLikesInteractor],
) -> IncomingLikesResponse:
    try:
        result = await interactor.execute()
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error

    items: list[IncomingLikeItemResponse] = []
    for item in result.items:
        card = item.candidate_card
        if card is None:
            items.append(
                IncomingLikeItemResponse(
                    liker_user_id=item.liker_user_id,
                    candidate_card=None,
                    reasons=item.reasons,
                ),
            )
            continue
        profile_response: IncomingLikeCandidateProfileResponse | None = None
        if card.profile is not None:
            profile_response = IncomingLikeCandidateProfileResponse(
                first_name=card.profile.first_name,
                last_name=card.profile.last_name,
                birth_date=card.profile.birth_date,
                gender=card.profile.gender.value,
                region=card.profile.region,
                avatar_url=card.profile.avatar_url,
            )
        dating_response: IncomingLikeCandidateDatingProfileResponse | None = None
        if card.dating_profile is not None:
            dating_response = IncomingLikeCandidateDatingProfileResponse(
                photos=card.dating_profile.photos,
                traits=[
                    IncomingLikeCandidateDatingTraitResponse(
                        trait_code=t.trait_code,
                        score=t.score,
                        is_hidden=t.is_hidden,
                    )
                    for t in card.dating_profile.traits
                ],
            )
        card_response = IncomingLikeCandidateCardResponse(
            user_id=card.user_id,
            profile=profile_response,
            dating_profile=dating_response,
        )
        items.append(
            IncomingLikeItemResponse(
                liker_user_id=item.liker_user_id,
                candidate_card=card_response,
                reasons=item.reasons,
            ),
        )
    return IncomingLikesResponse(items=items)


router = DishkaRouter(
    path="/likes",
    route_handlers=[get_my_incoming_likes],
    tags=["likes"],
)
