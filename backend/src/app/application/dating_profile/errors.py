class DatingProfileNotFoundError(Exception):
    pass


class DatingProfileValidationError(Exception):
    pass


class ProfileRequiredError(Exception):
    pass


class PhotoValidationError(Exception):
    pass


class PhotoModerationRejectedError(Exception):
    pass


class PhotoModerationUnavailableError(Exception):
    pass


class PhotoStorageUnavailableError(Exception):
    pass
