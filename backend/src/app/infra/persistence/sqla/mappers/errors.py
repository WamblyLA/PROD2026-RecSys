class MapperNotFoundError(LookupError):
    def __init__(self, entity_type: type) -> None:
        self.entity_type = entity_type
        super().__init__(f"No mapper registered for entity type: {entity_type!r}")
