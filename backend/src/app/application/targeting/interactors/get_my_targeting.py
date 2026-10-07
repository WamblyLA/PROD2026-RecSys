from datetime import UTC, datetime

from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.common.unit_of_work import UnitOfWork
from app.application.targeting.data_gateway import TargetingDataGateway
from app.application.targeting.dto import TargetingResult
from app.domain.targeting.entity import Targeting
from app.domain.targeting.value_objects import TargetGender, TargetingRules


@interactor
class GetMyTargetingInteractor:
    identity_provider: IdentityProvider
    targeting_data_gateway: TargetingDataGateway
    unit_of_work: UnitOfWork

    async def execute(self) -> TargetingResult:
        user = await self.identity_provider.get_current_user()
        targeting = await self.targeting_data_gateway.load_by_user_id(user.id)
        if targeting is None:
            age = 0
            region: str | None = None
            if user.profile is not None:
                today = datetime.now(tz=UTC).date()
                age = (
                    today.year
                    - user.profile.birth_date.year
                    - ((today.month, today.day) < (user.profile.birth_date.month, user.profile.birth_date.day))
                )
                region = user.profile.region
            rules = TargetingRules(
                region=region,
                gender_target=TargetGender.BOTH,
                age_from=max(0, age - 2),
                age_to=age + 2,
            )
            targeting = Targeting.factory(user.id, rules)
            await self.unit_of_work.add(targeting)
            await self.unit_of_work.commit()
        return TargetingResult(rules=targeting.rules)
