"""
Input validation utilities for TvDatafeed

This module provides validation functions for all user inputs to ensure
data integrity and provide clear error messages.
"""
from typing import Optional, Union
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
