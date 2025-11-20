"""
Unit tests for validators module
"""
import pytest
from tvDatafeed.validators import Validators
from tvDatafeed.exceptions import (
    DataValidationError,
    InvalidOHLCError,
    InvalidIntervalError,
    ConfigurationError
)


@pytest.mark.unit
class TestValidators:
    """Test Validators class"""

    def test_validate_symbol_valid(self):
        """Test validating valid symbols"""
        assert Validators.validate_symbol("BTCUSDT") == "BTCUSDT"
        assert Validators.validate_symbol("btcusdt") == "BTCUSDT"  # Uppercased
        assert Validators.validate_symbol("  BTCUSDT  ") == "BTCUSDT"  # Stripped

    def test_validate_symbol_formatted(self):
        """Test validating formatted symbols"""
        assert Validators.validate_symbol("BINANCE:BTCUSDT") == "BINANCE:BTCUSDT"
        assert Validators.validate_symbol("binance:btcusdt") == "BINANCE:BTCUSDT"

    def test_validate_symbol_invalid(self):
        """Test validating invalid symbols"""
        with pytest.raises(DataValidationError):
            Validators.validate_symbol("")

        with pytest.raises(DataValidationError):
            Validators.validate_symbol("BTC-USDT")  # Invalid character

        with pytest.raises(DataValidationError):
            Validators.validate_symbol("A" * 21)  # Too long

    def test_validate_exchange_valid(self):
        """Test validating valid exchanges"""
        assert Validators.validate_exchange("BINANCE") == "BINANCE"
        assert Validators.validate_exchange("binance") == "BINANCE"
        assert Validators.validate_exchange("  BINANCE  ") == "BINANCE"

    def test_validate_exchange_invalid(self):
        """Test validating invalid exchanges"""
        with pytest.raises(DataValidationError):
            Validators.validate_exchange("")

        with pytest.raises(DataValidationError):
            Validators.validate_exchange("BINANCE-US")  # Invalid character

    def test_validate_n_bars_valid(self):
        """Test validating valid n_bars"""
        assert Validators.validate_n_bars(10) == 10
        assert Validators.validate_n_bars(5000) == 5000

    def test_validate_n_bars_invalid(self):
        """Test validating invalid n_bars"""
        with pytest.raises(DataValidationError):
            Validators.validate_n_bars(0)

        with pytest.raises(DataValidationError):
            Validators.validate_n_bars(-10)

        with pytest.raises(DataValidationError):
            Validators.validate_n_bars(5001)  # Exceeds max

        with pytest.raises(DataValidationError):
            Validators.validate_n_bars("100")  # Wrong type

    def test_validate_interval_valid(self):
        """Test validating valid intervals"""
        assert Validators.validate_interval("1") == "1"
        assert Validators.validate_interval("1H") == "1H"
        assert Validators.validate_interval("1D") == "1D"

    def test_validate_interval_invalid(self):
        """Test validating invalid intervals"""
        with pytest.raises(InvalidIntervalError):
            Validators.validate_interval("10")

        with pytest.raises(InvalidIntervalError):
            Validators.validate_interval("1h")  # Wrong case

    def test_validate_timeout_valid(self):
        """Test validating valid timeouts"""
        assert Validators.validate_timeout(10.0) == 10.0
        assert Validators.validate_timeout(10) == 10.0
        assert Validators.validate_timeout(-1) == -1.0  # No timeout

    def test_validate_timeout_invalid(self):
        """Test validating invalid timeouts"""
        with pytest.raises(ConfigurationError):
            Validators.validate_timeout(-2)

        with pytest.raises(ConfigurationError):
            Validators.validate_timeout("invalid")

    def test_validate_ohlc_valid(self):
        """Test validating valid OHLC"""
        assert Validators.validate_ohlc(100, 105, 95, 102) is True

    def test_validate_ohlc_invalid_high(self):
        """Test validating OHLC with invalid high"""
        with pytest.raises(InvalidOHLCError):
            Validators.validate_ohlc(100, 99, 95, 102)  # high < close

    def test_validate_ohlc_invalid_low(self):
        """Test validating OHLC with invalid low"""
        with pytest.raises(InvalidOHLCError):
            Validators.validate_ohlc(100, 105, 101, 102)  # low > open

    def test_validate_ohlc_no_raise(self):
        """Test validating OHLC without raising"""
        assert Validators.validate_ohlc(100, 99, 95, 102, raise_on_error=False) is False
        assert Validators.validate_ohlc(100, 105, 95, 102, raise_on_error=False) is True

    def test_validate_volume_valid(self):
        """Test validating valid volume"""
        assert Validators.validate_volume(1000) is True
        assert Validators.validate_volume(0) is True

    def test_validate_volume_invalid(self):
        """Test validating invalid volume"""
        with pytest.raises(DataValidationError):
            Validators.validate_volume(-100)

        assert Validators.validate_volume(-100, raise_on_error=False) is False

    def test_validate_credentials_both(self):
        """Test validating when both credentials provided"""
        assert Validators.validate_credentials("user", "pass") is True

    def test_validate_credentials_neither(self):
        """Test validating when neither credential provided"""
        assert Validators.validate_credentials(None, None) is False

    def test_validate_credentials_only_username(self):
        """Test validating when only username provided"""
        with pytest.raises(ConfigurationError):
            Validators.validate_credentials("user", None)

    def test_validate_credentials_only_password(self):
        """Test validating when only password provided"""
        with pytest.raises(ConfigurationError):
            Validators.validate_credentials(None, "pass")

    def test_validate_credentials_empty_username(self):
        """Test validating with empty username"""
        with pytest.raises(ConfigurationError):
            Validators.validate_credentials("", "pass")

    def test_validate_credentials_empty_password(self):
        """Test validating with empty password"""
        with pytest.raises(ConfigurationError):
            Validators.validate_credentials("user", "")
