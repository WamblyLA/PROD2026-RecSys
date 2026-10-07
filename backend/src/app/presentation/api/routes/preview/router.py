from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import get

from app.application.preview.interactors.get_preview_cards import GetPreviewCardsInteractor
from app.presentation.api.routes.preview.dto import (
    PreviewCardDatingProfileResponse,
    PreviewCardDatingTraitResponse,
    PreviewCardProfileResponse,
    PreviewCardResponse,
    PreviewCardsResponse,
)


@get(
    path="/cards",
    summary="Get 5 random user cards (preview for jury)",
)
async def get_preview_cards(
    interactor: FromDishka[GetPreviewCardsInteractor],
) -> PreviewCardsResponse:
    result = await interactor.execute()
    cards: list[PreviewCardResponse] = []
    for card in result.cards:
        profile_resp: PreviewCardProfileResponse | None = None
        if card.profile is not None:
            profile_resp = PreviewCardProfileResponse(
                first_name=card.profile.first_name,
                last_name=card.profile.last_name,
                birth_date=card.profile.birth_date,
                gender=card.profile.gender.value,
                region=card.profile.region,
                avatar_url=card.profile.avatar_url,
            )
        dating_resp: PreviewCardDatingProfileResponse | None = None
        if card.dating_profile is not None:
            dating_resp = PreviewCardDatingProfileResponse(
                photos=card.dating_profile.photos,
                traits=[
                    PreviewCardDatingTraitResponse(
                        trait_code=t.trait_code,
                        score=t.score,
                        is_hidden=t.is_hidden,
                    )
                    for t in card.dating_profile.traits
                ],
            )
        cards.append(
            PreviewCardResponse(
                user_id=card.user_id,
                profile=profile_resp,
                dating_profile=dating_resp,
            ),
        )
    return PreviewCardsResponse(cards=cards)


router = DishkaRouter(
    path="/preview",
    route_handlers=[get_preview_cards],
    tags=["preview"],
)
