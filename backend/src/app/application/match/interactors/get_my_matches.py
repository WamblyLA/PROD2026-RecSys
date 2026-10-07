from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.application.interaction.blocked_pairs_gateway import BlockedPairsGateway
from app.application.match.data_gateway import MatchDataGateway
from app.application.match.dto import MatchesResult, MatchItem
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
class GetMyMatchesInteractor:
    identity_provider: IdentityProvider
    match_data_gateway: MatchDataGateway
    blocked_pairs_gateway: BlockedPairsGateway
    user_data_gateway: UserDataGateway
    dating_profile_data_gateway: DatingProfileDataGateway

    async def execute(self) -> MatchesResult:
        user = await self.identity_provider.get_current_user()
        match_user_ids = await self.match_data_gateway.list_active_match_user_ids(user.id)
        blocked_user_ids = await self.blocked_pairs_gateway.list_blocked_user_ids(user.id)
        match_user_ids = [uid for uid in match_user_ids if uid not in blocked_user_ids]
        if not match_user_ids:
            return MatchesResult(items=[])

        users = await self.user_data_gateway.load_many_with_ids(match_user_ids)
        users_by_id = {u.id: u for u in users}
        dating_profiles = await self.dating_profile_data_gateway.load_many_by_user_ids(match_user_ids)

        items: list[MatchItem] = []
        for candidate_user_id in match_user_ids:
            candidate = users_by_id.get(candidate_user_id)
            if candidate is None:
                continue
            dp = dating_profiles.get(candidate_user_id)
            card = _build_candidate_card(candidate, dp)
            items.append(
                MatchItem(
                    candidate_user_id=str(candidate_user_id),
                    candidate_card=card,
                ),
            )
        return MatchesResult(items=items)
