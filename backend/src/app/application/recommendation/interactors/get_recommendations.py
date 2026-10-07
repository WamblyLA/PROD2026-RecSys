from uuid import UUID

from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.common.unit_of_work import UnitOfWork
from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.application.interaction.blocked_pairs_gateway import BlockedPairsGateway
from app.application.profile.errors import ProfileNotFoundError
from app.application.recommendation.dto import (
    RecommendationCandidateCardItem,
    RecommendationCandidateDatingProfileItem,
    RecommendationCandidateDatingTraitItem,
    RecommendationCandidateProfileItem,
    RecommendationItem,
    RecommendationsResult,
)
from app.application.recommendation.errors import RecommendationCandidatesNotFoundError
from app.application.recommendation.protocol import RecommendationProvider
from app.application.user.data_gateway import UserDataGateway
from app.domain.recommendation.entity import Recommendation
from app.domain.recommendation.value_objects import RecommendationReason
from app.domain.user.entity import UserId


@interactor
class GetRecommendationsInteractor:
    identity_provider: IdentityProvider
    recommendation_provider: RecommendationProvider
    unit_of_work: UnitOfWork
    blocked_pairs_gateway: BlockedPairsGateway
    dating_profile_data_gateway: DatingProfileDataGateway
    user_data_gateway: UserDataGateway

    async def execute(self) -> RecommendationsResult:
        user = await self.identity_provider.get_current_user()
        dating_profile = await self.dating_profile_data_gateway.load_by_user_id(
            user.id,
        )
        if dating_profile is None or len(dating_profile.photos) < 1:
            raise ProfileNotFoundError

        items = await self.recommendation_provider.get_recommendations(user_id=user.id)
        blocked_user_ids = await self.blocked_pairs_gateway.list_blocked_user_ids(user.id)
        valid_items: list[tuple[RecommendationItem, UserId]] = []
        for item in items:
            candidate_user_id = _map_candidate_user_id(item.candidate_user_id)
            if candidate_user_id is None:
                continue
            if candidate_user_id in blocked_user_ids:
                continue
            valid_items.append((item, candidate_user_id))

        candidate_user_ids = [candidate_user_id for _, candidate_user_id in valid_items]
        users = await self.user_data_gateway.load_many_with_ids(candidate_user_ids)
        users_by_id = {candidate.id: candidate for candidate in users}
        missing_candidate_user_ids = [
            candidate_user_id for candidate_user_id in candidate_user_ids if candidate_user_id not in users_by_id
        ]
        if missing_candidate_user_ids:
            raise RecommendationCandidatesNotFoundError(missing_count=len(missing_candidate_user_ids))
        dating_profiles_by_user_id = await self.dating_profile_data_gateway.load_many_by_user_ids(
            candidate_user_ids,
        )

        result_items: list[RecommendationItem] = []
        for item, candidate_user_id in valid_items:
            recommendation = Recommendation.factory(
                ml_recommendation_id=item.ml_recommendation_id,
                user_id=user.id,
                candidate_user_id=candidate_user_id,
                reasons=[
                    RecommendationReason(
                        feature_name=feature_name,
                        score=score,
                    )
                    for feature_name, score in item.reasons.items()
                ],
            )
            await self.unit_of_work.add(recommendation)
            candidate = users_by_id.get(candidate_user_id)
            candidate_dating_profile = dating_profiles_by_user_id.get(candidate_user_id)
            candidate_card: RecommendationCandidateCardItem | None = None
            if candidate is not None:
                candidate_card = RecommendationCandidateCardItem(
                    user_id=str(candidate.id),
                    profile=(
                        RecommendationCandidateProfileItem(
                            first_name=candidate.profile.first_name,
                            last_name=candidate.profile.last_name,
                            birth_date=candidate.profile.birth_date,
                            gender=candidate.profile.gender,
                            region=candidate.profile.region,
                            avatar_url=candidate.profile.avatar_url,
                        )
                        if candidate.profile is not None
                        else None
                    ),
                    dating_profile=(
                        RecommendationCandidateDatingProfileItem(
                            photos=candidate_dating_profile.photos,
                            traits=[
                                RecommendationCandidateDatingTraitItem(
                                    trait_code=trait.trait_code,
                                    score=trait.score,
                                    is_hidden=trait.is_hidden,
                                )
                                for trait in candidate_dating_profile.traits
                            ],
                        )
                        if candidate_dating_profile is not None
                        else None
                    ),
                )
            result_items.append(
                RecommendationItem(
                    ml_recommendation_id=item.ml_recommendation_id,
                    user_id=item.user_id,
                    candidate_user_id=str(candidate_user_id),
                    reasons=item.reasons,
                    candidate_card=candidate_card,
                ),
            )
        await self.unit_of_work.commit()
        return RecommendationsResult(items=result_items)


def _map_candidate_user_id(raw_candidate_user_id: str) -> UserId | None:
    try:
        return UserId(UUID(raw_candidate_user_id))
    except ValueError:
        return None
