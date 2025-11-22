"""
Unit tests for exceptions module
"""
import pytest
from tvDatafeed.exceptions import (
    TvDatafeedError,
    AuthenticationError,
    TwoFactorRequiredError,
    CaptchaRequiredError,
    NetworkError,
    WebSocketError,
    WebSocketTimeoutError,
    ConnectionError,
    DataError,
    DataNotFoundError,
    DataValidationError,
    InvalidOHLCError,
    SymbolNotFoundError,
    InvalidIntervalError,
    ThreadingError,
    LockTimeoutError,
    ConsumerError,
    ConfigurationError,
    RateLimitError
)


@pytest.mark.unit
class TestTvDatafeedError:
    """Test base TvDatafeedError"""

    def test_base_exception(self):
        """Test creating base exception"""
        error = TvDatafeedError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)


@pytest.mark.unit
class TestAuthenticationErrors:
    """Test authentication-related exceptions"""

    def test_authentication_error_basic(self):
        """Test basic AuthenticationError"""
        error = AuthenticationError("Login failed")
        assert str(error) == "Login failed"
        assert error.username is None

    def test_authentication_error_with_username(self):
        """Test AuthenticationError with username"""
        error = AuthenticationError("Login failed", username="testuser")
        assert "testuser" in str(error)
        assert error.username == "testuser"

    def test_two_factor_required_error(self):
        """Test TwoFactorRequiredError"""
        error = TwoFactorRequiredError()
        assert "Two-factor authentication required" in str(error)
        assert error.method == "totp"

    def test_two_factor_required_error_custom_method(self):
        """Test TwoFactorRequiredError with custom method"""
        error = TwoFactorRequiredError(method="sms")
        assert "sms" in str(error)
        assert error.method == "sms"

    def test_captcha_required_error(self):
        """Test CaptchaRequiredError"""
        error = CaptchaRequiredError()
        assert "CAPTCHA" in str(error)
        assert "WORKAROUND" in str(error)
        assert "authToken" in str(error)
        assert error.username is None

    def test_captcha_required_error_with_username(self):
        """Test CaptchaRequiredError with username"""
        error = CaptchaRequiredError(username="testuser")
        assert error.username == "testuser"

    def test_authentication_error_inheritance(self):
        """Test that auth errors inherit properly"""
        assert issubclass(AuthenticationError, TvDatafeedError)
        assert issubclass(TwoFactorRequiredError, AuthenticationError)
        assert issubclass(CaptchaRequiredError, AuthenticationError)


@pytest.mark.unit
class TestNetworkErrors:
    """Test network-related exceptions"""

    def test_network_error(self):
        """Test NetworkError base class"""
        error = NetworkError("Network issue")
        assert str(error) == "Network issue"
        assert isinstance(error, TvDatafeedError)

    def test_websocket_error_basic(self):
        """Test basic WebSocketError"""
        error = WebSocketError("Connection failed")
        assert str(error) == "Connection failed"

    def test_websocket_error_with_url(self):
        """Test WebSocketError with URL"""
        error = WebSocketError("Connection failed", url="wss://example.com")
        assert "wss://example.com" in str(error)

    def test_websocket_timeout_error(self):
        """Test WebSocketTimeoutError"""
        error = WebSocketTimeoutError("connect", timeout=30.0)
        assert "connect" in str(error)
        assert "30" in str(error)
        assert "timed out" in str(error)

    def test_connection_error_basic(self):
        """Test basic ConnectionError"""
        error = ConnectionError("Connection refused")
        assert str(error) == "Connection refused"

    def test_connection_error_with_retry_count(self):
        """Test ConnectionError with retry count"""
        error = ConnectionError("Connection failed", retry_count=3)
        assert "3 retries" in str(error)

    def test_network_error_inheritance(self):
        """Test that network errors inherit properly"""
        assert issubclass(NetworkError, TvDatafeedError)
        assert issubclass(WebSocketError, NetworkError)
        assert issubclass(WebSocketTimeoutError, WebSocketError)
        assert issubclass(ConnectionError, NetworkError)


@pytest.mark.unit
class TestDataErrors:
    """Test data-related exceptions"""

    def test_data_error(self):
        """Test DataError base class"""
        error = DataError("Data issue")
        assert str(error) == "Data issue"
        assert isinstance(error, TvDatafeedError)

    def test_data_not_found_error(self):
        """Test DataNotFoundError"""
        error = DataNotFoundError("BTCUSDT", "BINANCE")
        assert "BTCUSDT" in str(error)
        assert "BINANCE" in str(error)
        assert error.symbol == "BTCUSDT"
        assert error.exchange == "BINANCE"
        # Should include helpful hints
        assert "search_symbol()" in str(error)

    def test_data_validation_error(self):
        """Test DataValidationError"""
        error = DataValidationError("n_bars", 0, "must be positive")
        assert "n_bars" in str(error)
        assert "0" in str(error)
        assert "must be positive" in str(error)
        assert error.field == "n_bars"
        assert error.value == 0
        assert error.reason == "must be positive"

    def test_invalid_ohlc_error(self):
        """Test InvalidOHLCError"""
        error = InvalidOHLCError(100, 99, 95, 102)
        assert "100" in str(error)
        assert "99" in str(error)
        assert "95" in str(error)
        assert "102" in str(error)
        # Should inherit from DataValidationError
        assert isinstance(error, DataValidationError)

    def test_symbol_not_found_error_basic(self):
        """Test basic SymbolNotFoundError"""
        error = SymbolNotFoundError("UNKNOWN")
        assert "UNKNOWN" in str(error)
        assert error.symbol == "UNKNOWN"
        assert error.exchange is None

    def test_symbol_not_found_error_with_exchange(self):
        """Test SymbolNotFoundError with exchange"""
        error = SymbolNotFoundError("UNKNOWN", exchange="BINANCE")
        assert "UNKNOWN" in str(error)
        assert "BINANCE" in str(error)
        assert error.exchange == "BINANCE"

    def test_invalid_interval_error_basic(self):
        """Test basic InvalidIntervalError"""
        error = InvalidIntervalError("10")
        assert "10" in str(error)
        assert error.interval == "10"

    def test_invalid_interval_error_with_supported(self):
        """Test InvalidIntervalError with supported list"""
        error = InvalidIntervalError("10", supported=["1", "5", "1H"])
        assert "10" in str(error)
        assert "1" in str(error)
        assert "5" in str(error)
        assert "1H" in str(error)

    def test_data_error_inheritance(self):
        """Test that data errors inherit properly"""
        assert issubclass(DataError, TvDatafeedError)
        assert issubclass(DataNotFoundError, DataError)
        assert issubclass(DataValidationError, DataError)
        assert issubclass(InvalidOHLCError, DataValidationError)
        assert issubclass(SymbolNotFoundError, DataError)
        assert issubclass(InvalidIntervalError, DataError)


@pytest.mark.unit
class TestThreadingErrors:
    """Test threading-related exceptions"""

    def test_threading_error(self):
        """Test ThreadingError base class"""
        error = ThreadingError("Thread issue")
        assert str(error) == "Thread issue"
        assert isinstance(error, TvDatafeedError)

    def test_lock_timeout_error(self):
        """Test LockTimeoutError"""
        error = LockTimeoutError(timeout=5.0, resource="_sat")
        assert "5" in str(error)
        assert "_sat" in str(error)
        assert error.timeout == 5.0
        assert error.resource == "_sat"

    def test_lock_timeout_error_default_resource(self):
        """Test LockTimeoutError with default resource"""
        error = LockTimeoutError(timeout=5.0)
        assert "resource" in str(error)
        assert error.resource == "resource"

    def test_consumer_error_basic(self):
        """Test basic ConsumerError"""
        error = ConsumerError("Callback failed")
        assert str(error) == "Callback failed"

    def test_consumer_error_with_seis(self):
        """Test ConsumerError with seis"""
        error = ConsumerError("Callback failed", seis="BTCUSDT_BINANCE_1H")
        assert "BTCUSDT_BINANCE_1H" in str(error)
        assert "Callback failed" in str(error)

    def test_threading_error_inheritance(self):
        """Test that threading errors inherit properly"""
        assert issubclass(ThreadingError, TvDatafeedError)
        assert issubclass(LockTimeoutError, ThreadingError)
        assert issubclass(ConsumerError, ThreadingError)


@pytest.mark.unit
class TestConfigurationError:
    """Test configuration-related exceptions"""

    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("timeout", -5, "must be non-negative")
        assert "timeout" in str(error)
        assert "-5" in str(error)
        assert "must be non-negative" in str(error)
        assert error.parameter == "timeout"
        assert error.value == -5
        assert error.reason == "must be non-negative"

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits properly"""
        assert issubclass(ConfigurationError, TvDatafeedError)


@pytest.mark.unit
class TestRateLimitError:
    """Test rate limit exception"""

    def test_rate_limit_error_default(self):
        """Test RateLimitError with default window"""
        error = RateLimitError(limit=100)
        assert "100" in str(error)
        assert "60" in str(error)  # Default window
        assert error.limit == 100
        assert error.window == 60

    def test_rate_limit_error_custom_window(self):
        """Test RateLimitError with custom window"""
        error = RateLimitError(limit=50, window=30)
        assert "50" in str(error)
        assert "30" in str(error)
        assert error.window == 30

    def test_rate_limit_error_inheritance(self):
        """Test that RateLimitError inherits properly"""
        assert issubclass(RateLimitError, NetworkError)


@pytest.mark.unit
class TestExceptionRaising:
    """Test raising and catching exceptions"""

    def test_catch_specific_exception(self):
        """Test catching specific exception"""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Test")

    def test_catch_base_exception(self):
        """Test catching base exception catches derived"""
        with pytest.raises(TvDatafeedError):
            raise WebSocketError("Test")

    def test_catch_parent_exception(self):
        """Test catching parent catches child"""
        with pytest.raises(NetworkError):
            raise WebSocketTimeoutError("Test", timeout=5.0)

    def test_exception_chaining(self):
        """Test exception chaining"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise WebSocketError("Wrapped error") from e
        except WebSocketError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)


@pytest.mark.unit
class TestExceptionMessages:
    """Test exception message formatting"""

    def test_captcha_error_includes_workaround(self):
        """Test CaptchaRequiredError includes detailed workaround"""
        error = CaptchaRequiredError()
        message = str(error)
        # Should include step-by-step instructions
        assert "browser" in message.lower()
        assert "devtools" in message.lower() or "DevTools" in message
        assert "cookie" in message.lower() or "Cookies" in message

    def test_data_not_found_includes_hints(self):
        """Test DataNotFoundError includes helpful hints"""
        error = DataNotFoundError("UNKNOWN", "BINANCE")
        message = str(error)
        # Should include possible causes
        assert "Symbol name incorrect" in message or "search_symbol" in message
        assert "exchange" in message.lower()

    def test_websocket_timeout_includes_timeout_value(self):
        """Test WebSocketTimeoutError includes timeout value"""
        error = WebSocketTimeoutError("connect", timeout=30.5)
        message = str(error)
        assert "30.5" in message or "30" in message
