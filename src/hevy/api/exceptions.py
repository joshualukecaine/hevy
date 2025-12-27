"""Custom exceptions for the Hevy API client."""


class HevyAPIError(Exception):
    """Base exception for Hevy API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: str = ""):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class HevyAuthenticationError(HevyAPIError):
    """Raised when API authentication fails."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class HevyRateLimitError(HevyAPIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class HevyNotFoundError(HevyAPIError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class HevyValidationError(HevyAPIError):
    """Raised when request validation fails."""

    def __init__(self, message: str = "Invalid request"):
        super().__init__(message, status_code=400)
