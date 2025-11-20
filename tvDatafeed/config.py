"""
Configuration module for TvDatafeed

This module centralizes all configuration parameters to avoid hardcoded values
and make the library more flexible and testable.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class NetworkConfig:
    """
    Network configuration for WebSocket and HTTP connections

    Attributes:
        ws_url: WebSocket URL for TradingView data feed
        ws_headers: Headers to send with WebSocket connection
        connect_timeout: Timeout for establishing connection (seconds)
        send_timeout: Timeout for sending messages (seconds)
        recv_timeout: Timeout for receiving messages (seconds)
        max_retries: Maximum number of retry attempts
        base_retry_delay: Initial delay between retries (seconds)
        max_retry_delay: Maximum delay between retries (seconds)
        requests_per_minute: Rate limit for requests
    """

    ws_url: str = "wss://data.tradingview.com/socket.io/websocket"
    ws_headers: Dict[str, str] = field(default_factory=lambda: {
        "Origin": "https://data.tradingview.com"
    })

    # Timeouts (in seconds)
    connect_timeout: float = 10.0
    send_timeout: float = 5.0
    recv_timeout: float = 30.0

    # Retry configuration
    max_retries: int = 3
    base_retry_delay: float = 2.0
    max_retry_delay: float = 60.0

    # Rate limiting
    requests_per_minute: int = 60

    @classmethod
    def from_env(cls) -> 'NetworkConfig':
        """
        Create NetworkConfig from environment variables

        Environment variables:
            TV_WS_URL: WebSocket URL
            TV_CONNECT_TIMEOUT: Connection timeout
            TV_SEND_TIMEOUT: Send timeout
            TV_RECV_TIMEOUT: Receive timeout
            TV_MAX_RETRIES: Maximum retry attempts
            TV_BASE_RETRY_DELAY: Base retry delay
            TV_MAX_RETRY_DELAY: Maximum retry delay
            TV_REQUESTS_PER_MINUTE: Rate limit

        Returns:
            NetworkConfig instance with values from environment
        """
        return cls(
            ws_url=os.getenv('TV_WS_URL', cls.ws_url),
            connect_timeout=float(os.getenv('TV_CONNECT_TIMEOUT', str(cls.connect_timeout))),
            send_timeout=float(os.getenv('TV_SEND_TIMEOUT', str(cls.send_timeout))),
            recv_timeout=float(os.getenv('TV_RECV_TIMEOUT', str(cls.recv_timeout))),
            max_retries=int(os.getenv('TV_MAX_RETRIES', str(cls.max_retries))),
            base_retry_delay=float(os.getenv('TV_BASE_RETRY_DELAY', str(cls.base_retry_delay))),
            max_retry_delay=float(os.getenv('TV_MAX_RETRY_DELAY', str(cls.max_retry_delay))),
            requests_per_minute=int(os.getenv('TV_REQUESTS_PER_MINUTE', str(cls.requests_per_minute))),
        )


@dataclass
class AuthConfig:
    """
    Authentication configuration

    Attributes:
        sign_in_url: TradingView sign-in endpoint
        signin_headers: Headers for authentication requests
        username: TradingView username (from env)
        password: TradingView password (from env)
        two_factor_code: 2FA code if required (from env)
    """

    sign_in_url: str = 'https://www.tradingview.com/accounts/signin/'
    signin_headers: Dict[str, str] = field(default_factory=lambda: {
        'Referer': 'https://www.tradingview.com'
    })

    username: Optional[str] = None
    password: Optional[str] = None
    two_factor_code: Optional[str] = None

    @classmethod
    def from_env(cls) -> 'AuthConfig':
        """
        Create AuthConfig from environment variables

        Environment variables:
            TV_USERNAME: TradingView username
            TV_PASSWORD: TradingView password
            TV_2FA_CODE: Two-factor authentication code

        Returns:
            AuthConfig instance with credentials from environment
        """
        return cls(
            username=os.getenv('TV_USERNAME'),
            password=os.getenv('TV_PASSWORD'),
            two_factor_code=os.getenv('TV_2FA_CODE'),
        )


@dataclass
class DataConfig:
    """
    Data processing configuration

    Attributes:
        max_bars: Maximum number of bars to fetch in one request
        default_bars: Default number of bars if not specified
        validate_data: Whether to validate OHLCV data
        fill_missing_volume: How to handle missing volume ('zero', 'forward', 'interpolate')
        timezone: Default timezone for datetime index
    """

    max_bars: int = 5000
    default_bars: int = 10
    validate_data: bool = True
    fill_missing_volume: str = 'zero'
    timezone: str = 'UTC'

    @classmethod
    def from_env(cls) -> 'DataConfig':
        """Create DataConfig from environment variables"""
        return cls(
            max_bars=int(os.getenv('TV_MAX_BARS', str(cls.max_bars))),
            default_bars=int(os.getenv('TV_DEFAULT_BARS', str(cls.default_bars))),
            validate_data=os.getenv('TV_VALIDATE_DATA', 'true').lower() == 'true',
            fill_missing_volume=os.getenv('TV_FILL_MISSING_VOLUME', cls.fill_missing_volume),
            timezone=os.getenv('TV_TIMEZONE', cls.timezone),
        )


@dataclass
class ThreadingConfig:
    """
    Threading configuration for TvDatafeedLive

    Attributes:
        retry_limit: Maximum retry attempts for data fetching
        retry_sleep: Sleep time between retries (seconds)
        shutdown_timeout: Timeout for graceful shutdown (seconds)
    """

    retry_limit: int = 50
    retry_sleep: float = 0.1
    shutdown_timeout: float = 10.0

    @classmethod
    def from_env(cls) -> 'ThreadingConfig':
        """Create ThreadingConfig from environment variables"""
        return cls(
            retry_limit=int(os.getenv('TV_RETRY_LIMIT', str(cls.retry_limit))),
            retry_sleep=float(os.getenv('TV_RETRY_SLEEP', str(cls.retry_sleep))),
            shutdown_timeout=float(os.getenv('TV_SHUTDOWN_TIMEOUT', str(cls.shutdown_timeout))),
        )


@dataclass
class TvDatafeedConfig:
    """
    Global configuration for TvDatafeed

    This is the main configuration class that aggregates all sub-configurations.

    Attributes:
        network: Network configuration
        auth: Authentication configuration
        data: Data processing configuration
        threading: Threading configuration
        debug: Enable debug mode
    """

    network: NetworkConfig = field(default_factory=NetworkConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    data: DataConfig = field(default_factory=DataConfig)
    threading: ThreadingConfig = field(default_factory=ThreadingConfig)
    debug: bool = False

    @classmethod
    def from_env(cls) -> 'TvDatafeedConfig':
        """
        Create complete configuration from environment variables

        Returns:
            TvDatafeedConfig instance with all sub-configs from environment
        """
        return cls(
            network=NetworkConfig.from_env(),
            auth=AuthConfig.from_env(),
            data=DataConfig.from_env(),
            threading=ThreadingConfig.from_env(),
            debug=os.getenv('TV_DEBUG', 'false').lower() == 'true',
        )

    @classmethod
    def default(cls) -> 'TvDatafeedConfig':
        """
        Create default configuration

        Returns:
            TvDatafeedConfig instance with default values
        """
        return cls()


# Global default configuration instance
DEFAULT_CONFIG = TvDatafeedConfig.default()
