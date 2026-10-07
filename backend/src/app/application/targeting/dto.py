from app.application.common.dto import dto
from app.domain.targeting.value_objects import TargetingRules


@dto
class TargetingResult:
    rules: TargetingRules
