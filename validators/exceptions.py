from validators.validation_error_type import ValidationErrorType


class ValidationException(Exception):
    def __init__(self, message, error_type, field=None, value=None):
        super().__init__(message)
        self.error_type = error_type
        self.field = field
        self.value = value


class StakeValidationException(ValidationException):
    def __init__(self, message, field=None, value=None):
        super().__init__(message, ValidationErrorType.STAKE_ERROR, field, value)


class BetValidationException(ValidationException):
    def __init__(self, message, field=None, value=None):
        super().__init__(message, ValidationErrorType.BET_ERROR, field, value)


class LimitValidationException(ValidationException):
    def __init__(self, message, field=None, value=None):
        super().__init__(message, ValidationErrorType.LIMIT_ERROR, field, value)


class ProbabilityValidationException(ValidationException):
    def __init__(self, message, field=None, value=None):
        super().__init__(message, ValidationErrorType.PROBABILITY_ERROR, field, value)