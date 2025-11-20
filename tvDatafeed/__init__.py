"""
TvDatafeed - TradingView data downloader

A Python library for downloading historical and real-time data from TradingView.
"""

# Core classes
from .main import TvDatafeed, Interval
from .datafeed import TvDatafeedLive
from .seis import Seis
from .consumer import Consumer

# Exceptions
from .exceptions import (
    TvDatafeedError,
    AuthenticationError,
    TwoFactorRequiredError,
    NetworkError,
    WebSocketError,
    WebSocketTimeoutError,
    ConnectionError,
    DataError,
    DataNotFoundError,
    DataValidationError,
    InvalidOHLCError,
    InvalidIntervalError,
    ThreadingError,
    LockTimeoutError,
    ConsumerError,
    ConfigurationError,
    RateLimitError
)

# Validators
from .validators import Validators

# Utilities
from .utils import (
    generate_session_id,
    generate_chart_session_id,
    retry_with_backoff,
    mask_sensitive_data,
    ContextTimer
)

__version__ = "2.1.0"

__all__ = [
    # Core classes
    'TvDatafeed',
    'TvDatafeedLive',
    'Interval',
    'Seis',
    'Consumer',
    # Exceptions
    'TvDatafeedError',
    'AuthenticationError',
    'TwoFactorRequiredError',
    'NetworkError',
    'WebSocketError',
    'WebSocketTimeoutError',
    'ConnectionError',
    'DataError',
    'DataNotFoundError',
    'DataValidationError',
    'InvalidOHLCError',
    'InvalidIntervalError',
    'ThreadingError',
    'LockTimeoutError',
    'ConsumerError',
    'ConfigurationError',
    'RateLimitError',
    # Validators
    'Validators',
    # Utilities
    'generate_session_id',
    'generate_chart_session_id',
    'retry_with_backoff',
    'mask_sensitive_data',
    'ContextTimer',
]
