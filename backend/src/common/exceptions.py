class DoesNotExistError(Exception):
    """Raised when a request entity is not found"""

class NotAllowedError(Exception):
    """Raised when an operation is not allowed"""

class InvalidOperationError(Exception):
    """Raised when the requested operation is invalid"""

class InvalidArgumentError(Exception):
    """Raised when an argument passed to a function is invalid"""