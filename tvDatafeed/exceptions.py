"""
Custom exceptions for TvDatafeed

This module defines all custom exceptions used throughout the library.
Using custom exceptions makes error handling more precise and provides
better error messages to users.
"""
from typing import Optional


class TvDatafeedError(Exception):
    """Base exception for all TvDatafeed errors"""
    pass


class AuthenticationError(TvDatafeedError):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed", username: Optional[str] = None):
        self.username = username
        if username:
            message = f"{message} for user '{username}'"
        super().__init__(message)


class TwoFactorRequiredError(AuthenticationError):
    """Raised when 2FA is required but not provided"""

    def __init__(self, method: str = "totp"):
        self.method = method
        message = (
            f"Two-factor authentication required ({method}). "
            f"Please provide a 2FA code using the 'two_factor_code' parameter."
        )
        super().__init__(message)


class NetworkError(TvDatafeedError):
    """Base class for network-related errors"""
    pass


class WebSocketError(NetworkError):
    """Raised when WebSocket connection fails"""

    def __init__(self, message: str = "WebSocket error", url: Optional[str] = None):
        if url:
            message = f"{message} (URL: {url})"
        super().__init__(message)


class WebSocketTimeoutError(WebSocketError):
    """Raised when WebSocket operation times out"""

    def __init__(self, operation: str = "operation", timeout: float = 0):
        message = f"WebSocket {operation} timed out after {timeout}s"
        super().__init__(message)


class ConnectionError(NetworkError):
    """Raised when connection cannot be established"""

    def __init__(self, message: str = "Connection failed", retry_count: int = 0):
        if retry_count > 0:
            message = f"{message} after {retry_count} retries"
        super().__init__(message)


class DataError(TvDatafeedError):
    """Base class for data-related errors"""
    pass


class DataNotFoundError(DataError):
    """Raised when no data is returned"""

    def __init__(self, symbol: str, exchange: str):
        self.symbol = symbol
        self.exchange = exchange
        message = (
            f"No data found for {symbol} on {exchange}. "
            f"Possible causes:\n"
            f"  1. Symbol name incorrect (use search_symbol() to find exact name)\n"
            f"  2. Symbol not available on this exchange\n"
            f"  3. Authentication required for this symbol"
        )
        super().__init__(message)


class DataValidationError(DataError):
    """Raised when data validation fails"""

    def __init__(self, field: str, value: any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        message = f"Data validation failed for {field}='{value}': {reason}"
        super().__init__(message)


class InvalidOHLCError(DataValidationError):
    """Raised when OHLC data is invalid"""

    def __init__(self, open_price: float, high: float, low: float, close: float):
        reason = (
            f"OHLC relationship violated: "
            f"O={open_price}, H={high}, L={low}, C={close}"
        )
        super().__init__("OHLC", f"{open_price}/{high}/{low}/{close}", reason)


class SymbolNotFoundError(DataError):
    """Raised when symbol is not found"""

    def __init__(self, symbol: str, exchange: Optional[str] = None):
        self.symbol = symbol
        self.exchange = exchange
        if exchange:
            message = f"Symbol '{symbol}' not found on {exchange}"
        else:
            message = f"Symbol '{symbol}' not found"
        super().__init__(message)


class InvalidIntervalError(DataError):
    """Raised when interval is invalid"""

    def __init__(self, interval: str, supported: list = None):
        self.interval = interval
        message = f"Invalid interval: '{interval}'"
        if supported:
            message += f". Supported intervals: {', '.join(supported)}"
        super().__init__(message)


class ThreadingError(TvDatafeedError):
    """Base class for threading-related errors"""
    pass


class LockTimeoutError(ThreadingError):
    """Raised when lock acquisition times out"""

    def __init__(self, timeout: float, resource: str = "resource"):
        self.timeout = timeout
        self.resource = resource
        message = f"Failed to acquire lock for {resource} within {timeout}s"
        super().__init__(message)


class ConsumerError(ThreadingError):
    """Raised when consumer encounters an error"""

    def __init__(self, message: str, seis: Optional[str] = None):
        if seis:
            message = f"Consumer error for {seis}: {message}"
        super().__init__(message)


class ConfigurationError(TvDatafeedError):
    """Raised when configuration is invalid"""

    def __init__(self, parameter: str, value: any, reason: str):
        self.parameter = parameter
        self.value = value
        self.reason = reason
        message = f"Invalid configuration for {parameter}='{value}': {reason}"
        super().__init__(message)


class RateLimitError(NetworkError):
    """Raised when rate limit is exceeded"""

    def __init__(self, limit: int, window: int = 60):
        self.limit = limit
        self.window = window
        message = (
            f"Rate limit exceeded: {limit} requests per {window}s. "
            f"Please wait before retrying."
        )
        super().__init__(message)
