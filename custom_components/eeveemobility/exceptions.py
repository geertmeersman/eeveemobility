"""Exceptions used by EeveeMobility."""


class EeveeMobilityException(Exception):
    """Base class for all exceptions raised by EeveeMobility."""

    pass


class EeveeMobilityServiceException(Exception):
    """Raised when service is not available."""

    pass


class BadCredentialsException(Exception):
    """Raised when credentials are incorrect."""

    pass


class NotAuthenticatedException(Exception):
    """Raised when session is invalid."""

    pass


class GatewayTimeoutException(EeveeMobilityServiceException):
    """Raised when server times out."""

    pass


class BadGatewayException(EeveeMobilityServiceException):
    """Raised when server returns Bad Gateway."""

    pass
