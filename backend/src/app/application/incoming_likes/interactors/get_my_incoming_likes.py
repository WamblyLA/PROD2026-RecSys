from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.application.incoming_likes.data_gateway import IncomingLikesDataGateway
from app.application.incoming_likes.dto import IncomingLikeItem, IncomingLikesResult
from app.application.interaction.blocked_pairs_gateway import BlockedPairsGateway
from app.application.recommendation.data_gateway import RecommendationDataGateway
from app.application.recommendation.dto import (
    RecommendationCandidateCardItem,
    RecommendationCandidateDatingProfileItem,
    RecommendationCandidateDatingTraitItem,
    RecommendationCandidateProfileItem,
)
from app.application.user.data_gateway import UserDataGateway
from app.domain.dating_profile.entity import DatingProfile
from app.domain.user.entity import User


def _build_candidate_card(
    candidate: User,
    dating_profile: DatingProfile | None,
) -> RecommendationCandidateCardItem:
    profile_item: RecommendationCandidateProfileItem | None = None
    if candidate.profile is not None:
        profile_item = RecommendationCandidateProfileItem(
            first_name=candidate.profile.first_name,
            last_name=candidate.profile.last_name,
            birth_date=candidate.profile.birth_date,
            gender=candidate.profile.gender,
            region=candidate.profile.region,
            avatar_url=candidate.profile.avatar_url,
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
        user_id=str(candidate.id),
        profile=profile_item,
        dating_profile=dating_item,
    )


@interactor
class GetMyIncomingLikesInteractor:
    identity_provider: IdentityProvider
    incoming_likes_data_gateway: IncomingLikesDataGateway
    blocked_pairs_gateway: BlockedPairsGateway
    user_data_gateway: UserDataGateway
    dating_profile_data_gateway: DatingProfileDataGateway
    recommendation_data_gateway: RecommendationDataGateway

    async def execute(self) -> IncomingLikesResult:
        user = await self.identity_provider.get_current_user()
        liker_user_ids = await self.incoming_likes_data_gateway.list_liker_user_ids(user.id)
        blocked_user_ids = await self.blocked_pairs_gateway.list_blocked_user_ids(user.id)
        liker_user_ids = [uid for uid in liker_user_ids if uid not in blocked_user_ids]
        if not liker_user_ids:
            return IncomingLikesResult(items=[])

        users = await self.user_data_gateway.load_many_with_ids(liker_user_ids)
        users_by_id = {u.id: u for u in users}
        dating_profiles = await self.dating_profile_data_gateway.load_many_by_user_ids(liker_user_ids)

        items: list[IncomingLikeItem] = []
        for liker_user_id in liker_user_ids:
            candidate = users_by_id.get(liker_user_id)
            if candidate is None:
                continue
            dp = dating_profiles.get(liker_user_id)
            card = _build_candidate_card(candidate, dp)

            rec = await self.recommendation_data_gateway.load_latest_for_pair(
                user_id=user.id,
                candidate_user_id=liker_user_id,
            )

            items.append(
                IncomingLikeItem(
                    liker_user_id=str(liker_user_id),
                    candidate_card=card,
                    reasons=rec.reasons if rec is not None else None,
                ),
            )
        return IncomingLikesResult(items=items)
