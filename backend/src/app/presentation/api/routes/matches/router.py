from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import get
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_401_UNAUTHORIZED

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.match.interactors.get_my_matches import GetMyMatchesInteractor
from app.presentation.api.routes.matches.dto import (
    MatchCandidateCardResponse,
    MatchCandidateDatingProfileResponse,
    MatchCandidateDatingTraitResponse,
    MatchCandidateProfileResponse,
    MatchesResponse,
    MatchItemResponse,
)


@get(
    path="/me",
    summary="Get own active matches",
    security=[{"BearerToken": []}],
)
async def get_my_matches(
    interactor: FromDishka[GetMyMatchesInteractor],
) -> MatchesResponse:
    try:
        result = await interactor.execute()
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error

    items: list[MatchItemResponse] = []
    for match in result.items:
        card = match.candidate_card
        if card is None:
            items.append(
                MatchItemResponse(candidate_user_id=match.candidate_user_id, candidate_card=None),
            )
            continue
        profile_response: MatchCandidateProfileResponse | None = None
        if card.profile is not None:
            profile_response = MatchCandidateProfileResponse(
                first_name=card.profile.first_name,
                last_name=card.profile.last_name,
                birth_date=card.profile.birth_date,
                gender=card.profile.gender.value,
                region=card.profile.region,
                avatar_url=card.profile.avatar_url,
            )
        dating_response: MatchCandidateDatingProfileResponse | None = None
        if card.dating_profile is not None:
            dating_response = MatchCandidateDatingProfileResponse(
                photos=card.dating_profile.photos,
                traits=[
                    MatchCandidateDatingTraitResponse(
                        trait_code=t.trait_code,
                        score=t.score,
                        is_hidden=t.is_hidden,
                    )
                    for t in card.dating_profile.traits
                ],
            )
        card_response = MatchCandidateCardResponse(
            user_id=card.user_id,
            profile=profile_response,
            dating_profile=dating_response,
        )
        items.append(
            MatchItemResponse(
                candidate_user_id=match.candidate_user_id,
                candidate_card=card_response,
            ),
        )
    return MatchesResponse(items=items)


router = DishkaRouter(
    path="/matches",
    route_handlers=[get_my_matches],
    tags=["matches"],
)
