class TargetingNotFoundError(Exception):
    pass


class TargetingValidationError(Exception):
    """Targeting rules validation failed (e.g. age_from/age_to)."""
