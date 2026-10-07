from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.common.unit_of_work import UnitOfWork
from app.application.targeting.data_gateway import TargetingDataGateway
from app.application.targeting.dto import TargetingResult
from app.application.targeting.errors import TargetingValidationError
from app.domain.targeting.entity import Targeting
from app.domain.targeting.value_objects import TargetGender, TargetingRules


def _validate_rules(rules: TargetingRules) -> None:
    if rules.age_from < 0:
        raise TargetingValidationError
    if rules.age_to < rules.age_from:
        raise TargetingValidationError


@interactor
class UpsertMyTargetingInteractor:
    identity_provider: IdentityProvider
    targeting_data_gateway: TargetingDataGateway
    unit_of_work: UnitOfWork

    async def execute(
        self,
        region: str | None,
        gender_target: str,
        age_from: int,
        age_to: int,
    ) -> TargetingResult:
        try:
            gt = TargetGender(gender_target)
        except ValueError as err:
            raise TargetingValidationError from err
        rules = TargetingRules(
            region=region,
            gender_target=gt,
            age_from=age_from,
            age_to=age_to,
        )
        _validate_rules(rules)
        user = await self.identity_provider.get_current_user()
        existing = await self.targeting_data_gateway.load_by_user_id(user.id)
        if existing is not None:
            targeting = Targeting(
                id=user.id,
                created_at=existing.created_at,
                deleted_at=existing.deleted_at,
                rules=rules,
            )
        else:
            targeting = Targeting.factory(user.id, rules)
        await self.unit_of_work.add(targeting)
        await self.unit_of_work.commit()
        return TargetingResult(rules=rules)
