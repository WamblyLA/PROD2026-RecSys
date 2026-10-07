class ChatNotFoundError(Exception):
    pass


class ChatAccessDeniedError(Exception):
    pass


class ChatBlockedError(Exception):
    pass


class ChatNoActiveMatchError(Exception):
    pass


class ChatValidationError(Exception):
    pass
