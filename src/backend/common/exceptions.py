from functools import partial


class DoesNotExistError(Exception):
    """Raised when a request entity is not found"""


class NotAllowedError(Exception):
    """Raised when an operation is not allowed"""


class InvalidOperationError(Exception):
    """Raised when the requested operation is invalid"""


class InvalidArgumentError(Exception):
    """Raised when an argument passed to a function is invalid"""


# Error handler for Flask
def handle_errors(code, ex):
    return ex.args[0], code


APP_ERROR_STATUS_CODES = {
    DoesNotExistError: 404,
    NotAllowedError: 403,
    InvalidOperationError: 400,
    InvalidArgumentError: 400,
}

APP_ERROR_HANDLERS = {ex: partial(handle_errors, code) for ex, code in APP_ERROR_STATUS_CODES.items()}
