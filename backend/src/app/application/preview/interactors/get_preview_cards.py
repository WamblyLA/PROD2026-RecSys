from app.application.common.interactor import interactor
from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.application.preview.dto import PreviewCardsResult
from app.application.recommendation.dto import (
    RecommendationCandidateCardItem,
    RecommendationCandidateDatingProfileItem,
    RecommendationCandidateDatingTraitItem,
    RecommendationCandidateProfileItem,
)
from app.application.user.data_gateway import UserDataGateway
from app.domain.dating_profile.entity import DatingProfile
from app.domain.user.entity import User

PREVIEW_LIMIT = 5


def _build_card(user: User, dating_profile: DatingProfile | None) -> RecommendationCandidateCardItem:
    profile_item: RecommendationCandidateProfileItem | None = None
    if user.profile is not None:
        profile_item = RecommendationCandidateProfileItem(
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            birth_date=user.profile.birth_date,
            gender=user.profile.gender,
            region=user.profile.region,
            avatar_url=user.profile.avatar_url,
        )
    traits = [
        RecommendationCandidateDatingTraitItem(
            trait_code=t.trait_code,
            score=t.score,
            is_hidden=t.is_hidden,
        )
        for t in (dating_profile.traits if dating_profile else [])
    ]
    dating_item: RecommendationCandidateDatingProfileItem | None = None
    if dating_profile is not None and (dating_profile.photos or traits):
        dating_item = RecommendationCandidateDatingProfileItem(
            photos=dating_profile.photos,
            traits=traits,
        )
    return RecommendationCandidateCardItem(
        user_id=str(user.id),
        profile=profile_item,
        dating_profile=dating_item,
    )


@interactor
class GetPreviewCardsInteractor:
    user_data_gateway: UserDataGateway
    dating_profile_data_gateway: DatingProfileDataGateway

    async def execute(self) -> PreviewCardsResult:
        user_ids = await self.user_data_gateway.list_random_user_ids(limit=PREVIEW_LIMIT)
        if not user_ids:
            return PreviewCardsResult(cards=[])
        users = await self.user_data_gateway.load_many_with_ids(user_ids)
        dating_profiles = await self.dating_profile_data_gateway.load_many_by_user_ids(user_ids)
        cards = [_build_card(user, dating_profiles.get(user.id)) for user in users]
        return PreviewCardsResult(cards=cards)
