"""
Input validation utilities for TvDatafeed

This module provides validation functions for all user inputs to ensure
data integrity and provide clear error messages.
"""
from typing import Optional, Union
import datetime
import re
from .exceptions import (
    DataValidationError,
    InvalidOHLCError,
    InvalidIntervalError,
    ConfigurationError
)


class Validators:
    """Collection of validation methods"""

    # Regex patterns
    SYMBOL_PATTERN = re.compile(r'^[A-Z0-9]{1,20}$')
    EXCHANGE_PATTERN = re.compile(r'^[A-Z0-9]{1,20}$')

    # Valid intervals
    VALID_INTERVALS = [
        "1", "3", "5", "15", "30", "45",  # Minutes
        "1H", "2H", "3H", "4H",            # Hours
        "1D", "1W", "1M"                   # Day, Week, Month
    ]

    @staticmethod
    def validate_symbol(symbol: str, allow_formatted: bool = True) -> str:
        """
        Validate symbol name

        Parameters
        ----------
        symbol : str
            Symbol to validate. Can be in format "SYMBOL" or "EXCHANGE:SYMBOL"
        allow_formatted : bool
            Whether to allow already formatted symbols (e.g., "BINANCE:BTCUSDT")

        Returns
        -------
        str
            Validated symbol

        Raises
        ------
        DataValidationError
            If symbol is invalid

        Notes
        -----
        - Symbol format "EXCHANGE:SYMBOL" is preferred for reliability
        - If symbol has no exchange prefix, one must be provided in get_hist()
        - Common exchanges: BINANCE, NASDAQ, NSE, COINBASE, etc.
        """
        if not symbol or not isinstance(symbol, str):
            raise DataValidationError("symbol", symbol, "Symbol must be a non-empty string")

        symbol = symbol.strip().upper()

        # Allow formatted symbols (EXCHANGE:SYMBOL)
        if allow_formatted and ':' in symbol:
            parts = symbol.split(':')
            if len(parts) != 2:
                raise DataValidationError(
                    "symbol", symbol,
                    "Formatted symbol must be EXCHANGE:SYMBOL (e.g., 'BINANCE:BTCUSDT')"
                )

            # Validate both parts
            exchange_part, symbol_part = parts
            if not Validators.EXCHANGE_PATTERN.match(exchange_part):
                raise DataValidationError(
                    "symbol", symbol,
                    f"Exchange '{exchange_part}' must be alphanumeric, 1-20 characters"
                )
            if not Validators.SYMBOL_PATTERN.match(symbol_part):
                raise DataValidationError(
                    "symbol", symbol,
                    f"Symbol '{symbol_part}' must be alphanumeric, 1-20 characters"
                )

            return symbol

        # Validate simple symbol
        if not Validators.SYMBOL_PATTERN.match(symbol):
            raise DataValidationError(
                "symbol", symbol,
                "Symbol must be alphanumeric, 1-20 characters. "
                "TIP: Use format 'EXCHANGE:SYMBOL' (e.g., 'BINANCE:BTCUSDT') for better reliability."
            )

        return symbol

    @staticmethod
    def validate_exchange(exchange: str) -> str:
        """
        Validate exchange name

        Parameters
        ----------
        exchange : str
            Exchange to validate

        Returns
        -------
        str
            Validated exchange

        Raises
        ------
        DataValidationError
            If exchange is invalid
        """
        if not exchange or not isinstance(exchange, str):
            raise DataValidationError("exchange", exchange, "Exchange must be a non-empty string")

        exchange = exchange.strip().upper()

        if not Validators.EXCHANGE_PATTERN.match(exchange):
            raise DataValidationError(
                "exchange", exchange,
                "Exchange must be alphanumeric, 1-20 characters"
            )

        return exchange

    @staticmethod
    def validate_n_bars(n_bars: int, max_bars: int = 5000) -> int:
        """
        Validate number of bars

        Parameters
        ----------
        n_bars : int
            Number of bars to validate
        max_bars : int
            Maximum allowed bars

        Returns
        -------
        int
            Validated n_bars

        Raises
        ------
        DataValidationError
            If n_bars is invalid
        """
        if not isinstance(n_bars, int):
            raise DataValidationError("n_bars", n_bars, "n_bars must be an integer")

        if n_bars <= 0:
            raise DataValidationError("n_bars", n_bars, "n_bars must be positive")

        if n_bars > max_bars:
            raise DataValidationError(
                "n_bars", n_bars,
                f"n_bars cannot exceed {max_bars} (TradingView limit)"
            )

        return n_bars

    @staticmethod
    def validate_interval(interval: str) -> str:
        """
        Validate interval

        Parameters
        ----------
        interval : str
            Interval to validate

        Returns
        -------
        str
            Validated interval

        Raises
        ------
        InvalidIntervalError
            If interval is invalid
        """
        if interval not in Validators.VALID_INTERVALS:
            raise InvalidIntervalError(interval, Validators.VALID_INTERVALS)

        return interval

    @staticmethod
    def validate_timeout(timeout: Union[int, float]) -> float:
        """
        Validate timeout value

        Parameters
        ----------
        timeout : int or float
            Timeout in seconds (-1 for no timeout)

        Returns
        -------
        float
            Validated timeout

        Raises
        ------
        ConfigurationError
            If timeout is invalid
        """
        try:
            timeout = float(timeout)
        except (TypeError, ValueError):
            raise ConfigurationError("timeout", timeout, "Timeout must be a number")

        if timeout < -1:
            raise ConfigurationError("timeout", timeout, "Timeout must be >= -1")

        return timeout

    @staticmethod
    def validate_ohlc(
        open_price: float,
        high: float,
        low: float,
        close: float,
        raise_on_error: bool = True
    ) -> bool:
        """
        Validate OHLC relationship

        The high should be >= max(open, close) and
        the low should be <= min(open, close)

        Parameters
        ----------
        open_price : float
            Open price
        high : float
            High price
        low : float
            Low price
        close : float
            Close price
        raise_on_error : bool
            Whether to raise exception on error

        Returns
        -------
        bool
            True if valid, False if invalid (when raise_on_error=False)

        Raises
        ------
        InvalidOHLCError
            If OHLC is invalid and raise_on_error=True
        """
        # Check high >= max(open, close)
        max_oc = max(open_price, close)
        if high < max_oc:
            if raise_on_error:
                raise InvalidOHLCError(open_price, high, low, close)
            return False

        # Check low <= min(open, close)
        min_oc = min(open_price, close)
        if low > min_oc:
            if raise_on_error:
                raise InvalidOHLCError(open_price, high, low, close)
            return False

        return True

    @staticmethod
    def validate_volume(volume: float, raise_on_error: bool = True) -> bool:
        """
        Validate volume (must be non-negative)

        Parameters
        ----------
        volume : float
            Volume to validate
        raise_on_error : bool
            Whether to raise exception on error

        Returns
        -------
        bool
            True if valid, False if invalid

        Raises
        ------
        DataValidationError
            If volume is invalid and raise_on_error=True
        """
        if volume < 0:
            if raise_on_error:
                raise DataValidationError("volume", volume, "Volume cannot be negative")
            return False

        return True

    @staticmethod
    def validate_credentials(username: Optional[str], password: Optional[str]) -> bool:
        """
        Validate authentication credentials

        Parameters
        ----------
        username : str or None
            Username to validate
        password : str or None
            Password to validate

        Returns
        -------
        bool
            True if both provided, False if neither provided

        Raises
        ------
        ConfigurationError
            If only one credential is provided
        """
        if username is None and password is None:
            return False

        if username is None:
            raise ConfigurationError("username", None, "Username required when password is provided")

        if password is None:
            raise ConfigurationError("password", None, "Password required when username is provided")

        if not isinstance(username, str) or not username.strip():
            raise ConfigurationError("username", username, "Username must be a non-empty string")

        if not isinstance(password, str) or not password.strip():
            raise ConfigurationError("password", "***", "Password must be a non-empty string")

        return True

    @staticmethod
    def validate_date_range(
        start_date: Optional[datetime.datetime],
        end_date: Optional[datetime.datetime]
    ) -> tuple:
        """
        Validate date range for historical data query

        Parameters
        ----------
        start_date : datetime or None
            Start date for the query
        end_date : datetime or None
            End date for the query

        Returns
        -------
        tuple
            (start_date, end_date) if valid

        Raises
        ------
        DataValidationError
            If date range is invalid

        Notes
        -----
        Validation checks:
        - Both dates must be provided together (or both None)
        - Start date must be before end date
        - Neither date can be in the future
        - Both dates must be after 2000-01-01
        - Dates can be timezone-aware or naive
        """
        # Both must be provided or both must be None
        if (start_date is None) != (end_date is None):
            raise DataValidationError(
                "date_range",
                f"start={start_date}, end={end_date}",
                "Both start_date and end_date must be provided together"
            )

        # If both None, return them as-is
        if start_date is None and end_date is None:
            return None, None

        # Validate types
        if not isinstance(start_date, datetime.datetime):
            raise DataValidationError(
                "start_date",
                start_date,
                f"start_date must be a datetime object, got {type(start_date).__name__}"
            )

        if not isinstance(end_date, datetime.datetime):
            raise DataValidationError(
                "end_date",
                end_date,
                f"end_date must be a datetime object, got {type(end_date).__name__}"
            )

        # Get current time
        now = datetime.datetime.now()

        # Check start < end
        if start_date >= end_date:
            raise DataValidationError(
                "date_range",
                f"start={start_date}, end={end_date}",
                f"start_date ({start_date}) must be before end_date ({end_date})"
            )

        # Check dates are not in the future
        if start_date > now:
            raise DataValidationError(
                "start_date",
                start_date,
                f"start_date ({start_date}) cannot be in the future"
            )

        if end_date > now:
            raise DataValidationError(
                "end_date",
                end_date,
                f"end_date ({end_date}) cannot be in the future"
            )

        # Check dates are after 2000-01-01 (TradingView limitation)
        min_date = datetime.datetime(2000, 1, 1)
        if start_date < min_date:
            raise DataValidationError(
                "start_date",
                start_date,
                f"start_date ({start_date}) must be after 2000-01-01 (TradingView limitation)"
            )

        if end_date < min_date:
            raise DataValidationError(
                "end_date",
                end_date,
                f"end_date ({end_date}) must be after 2000-01-01 (TradingView limitation)"
            )

        return start_date, end_date

    @staticmethod
    def validate_timestamp(timestamp: Union[int, float], param_name: str = "timestamp") -> int:
        """
        Validate Unix timestamp (seconds or milliseconds)

        Parameters
        ----------
        timestamp : int or float
            Unix timestamp to validate
        param_name : str
            Parameter name for error messages

        Returns
        -------
        int
            Validated timestamp in milliseconds

        Raises
        ------
        DataValidationError
            If timestamp is invalid

        Notes
        -----
        - Accepts both seconds and milliseconds
        - Automatically converts seconds to milliseconds if needed
        - Validates timestamp is not in the future
        - Validates timestamp is after 2000-01-01
        """
        try:
            timestamp = int(timestamp)
        except (TypeError, ValueError):
            raise DataValidationError(
                param_name,
                timestamp,
                f"{param_name} must be a valid integer or float"
            )

        # Convert seconds to milliseconds if needed
        # Timestamps in seconds are typically < 10^10, milliseconds > 10^12
        if timestamp < 10**10:
            # Likely in seconds, convert to milliseconds
            timestamp = timestamp * 1000

        # Validate timestamp is after 2000-01-01
        min_timestamp = int(datetime.datetime(2000, 1, 1).timestamp() * 1000)
        if timestamp < min_timestamp:
            raise DataValidationError(
                param_name,
                timestamp,
                f"{param_name} must be after 2000-01-01 (TradingView limitation)"
            )

        # Validate timestamp is not in the future
        now_timestamp = int(datetime.datetime.now().timestamp() * 1000)
        if timestamp > now_timestamp:
            raise DataValidationError(
                param_name,
                timestamp,
                f"{param_name} cannot be in the future"
            )

        return timestamp


# Convenience functions for quick validation
def validate_symbol(symbol: str) -> str:
    """Validate symbol (convenience function)"""
    return Validators.validate_symbol(symbol)


def validate_exchange(exchange: str) -> str:
    """Validate exchange (convenience function)"""
    return Validators.validate_exchange(exchange)


def validate_n_bars(n_bars: int) -> int:
    """Validate n_bars (convenience function)"""
    return Validators.validate_n_bars(n_bars)


def validate_ohlc(open_price: float, high: float, low: float, close: float) -> bool:
    """Validate OHLC (convenience function)"""
    return Validators.validate_ohlc(open_price, high, low, close)
