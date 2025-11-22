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

    def test_validate_symbol_formatted_validates_parts(self):
        """Test that formatted symbols validate both exchange and symbol parts"""
        # Valid formatted symbol
        assert Validators.validate_symbol("NASDAQ:AAPL") == "NASDAQ:AAPL"

        # Invalid exchange part
        with pytest.raises(DataValidationError, match="Exchange .* must be alphanumeric"):
            Validators.validate_symbol("NASDAQ-US:AAPL")

        # Invalid symbol part
        with pytest.raises(DataValidationError, match="Symbol .* must be alphanumeric"):
            Validators.validate_symbol("NASDAQ:AAPL-USD")

        # Too many colons
        with pytest.raises(DataValidationError, match="Formatted symbol must be EXCHANGE:SYMBOL"):
            Validators.validate_symbol("NASDAQ:AAPL:USD")

    def test_validate_symbol_includes_tip_message(self):
        """Test that validation error for simple symbol includes format tip"""
        with pytest.raises(DataValidationError, match="TIP: Use format 'EXCHANGE:SYMBOL'"):
            Validators.validate_symbol("BTC-USD")  # Invalid character triggers helpful message

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


@pytest.mark.unit
class TestValidateDateRange:
    """Test date range validation"""

    def test_validate_date_range_valid(self):
        """Test validating valid date range"""
        import datetime
        start = datetime.datetime(2024, 1, 1)
        end = datetime.datetime(2024, 1, 15)

        result = Validators.validate_date_range(start, end)
        assert result == (start, end)

    def test_validate_date_range_both_none(self):
        """Test validating when both dates are None"""
        result = Validators.validate_date_range(None, None)
        assert result == (None, None)

    def test_validate_date_range_only_start(self):
        """Test validating when only start date provided"""
        import datetime
        start = datetime.datetime(2024, 1, 1)

        with pytest.raises(DataValidationError, match="Both start_date and end_date must be provided together"):
            Validators.validate_date_range(start, None)

    def test_validate_date_range_only_end(self):
        """Test validating when only end date provided"""
        import datetime
        end = datetime.datetime(2024, 1, 15)

        with pytest.raises(DataValidationError, match="Both start_date and end_date must be provided together"):
            Validators.validate_date_range(None, end)

    def test_validate_date_range_start_after_end(self):
        """Test validating when start is after end"""
        import datetime
        start = datetime.datetime(2024, 1, 15)
        end = datetime.datetime(2024, 1, 1)

        with pytest.raises(DataValidationError, match="must be before end_date"):
            Validators.validate_date_range(start, end)

    def test_validate_date_range_start_equals_end(self):
        """Test validating when start equals end"""
        import datetime
        date = datetime.datetime(2024, 1, 15)

        with pytest.raises(DataValidationError, match="must be before end_date"):
            Validators.validate_date_range(date, date)

    def test_validate_date_range_future_start(self):
        """Test validating when start date is in the future"""
        import datetime
        future = datetime.datetime.now() + datetime.timedelta(days=30)
        end = datetime.datetime.now() + datetime.timedelta(days=60)

        with pytest.raises(DataValidationError, match="cannot be in the future"):
            Validators.validate_date_range(future, end)

    def test_validate_date_range_future_end(self):
        """Test validating when end date is in the future"""
        import datetime
        start = datetime.datetime(2024, 1, 1)
        end = datetime.datetime.now() + datetime.timedelta(days=30)

        with pytest.raises(DataValidationError, match="cannot be in the future"):
            Validators.validate_date_range(start, end)

    def test_validate_date_range_before_2000_start(self):
        """Test validating when start date is before 2000"""
        import datetime
        start = datetime.datetime(1999, 12, 31)
        end = datetime.datetime(2024, 1, 15)

        with pytest.raises(DataValidationError, match="must be after 2000-01-01"):
            Validators.validate_date_range(start, end)

    def test_validate_date_range_before_2000_end(self):
        """Test validating when end date is before 2000"""
        import datetime
        start = datetime.datetime(1999, 6, 1)
        end = datetime.datetime(1999, 12, 31)

        with pytest.raises(DataValidationError, match="must be after 2000-01-01"):
            Validators.validate_date_range(start, end)

    def test_validate_date_range_invalid_start_type(self):
        """Test validating with non-datetime start"""
        import datetime
        end = datetime.datetime(2024, 1, 15)

        with pytest.raises(DataValidationError, match="must be a datetime object"):
            Validators.validate_date_range("2024-01-01", end)

    def test_validate_date_range_invalid_end_type(self):
        """Test validating with non-datetime end"""
        import datetime
        start = datetime.datetime(2024, 1, 1)

        with pytest.raises(DataValidationError, match="must be a datetime object"):
            Validators.validate_date_range(start, "2024-01-15")


@pytest.mark.unit
class TestValidateTimestamp:
    """Test timestamp validation"""

    def test_validate_timestamp_seconds(self):
        """Test validating timestamp in seconds"""
        # 2024-01-15 00:00:00 UTC
        timestamp_seconds = 1705276800

        result = Validators.validate_timestamp(timestamp_seconds)
        # Should be converted to milliseconds
        assert result == timestamp_seconds * 1000

    def test_validate_timestamp_milliseconds(self):
        """Test validating timestamp in milliseconds"""
        # Already in milliseconds
        timestamp_ms = 1705276800000

        result = Validators.validate_timestamp(timestamp_ms)
        assert result == timestamp_ms

    def test_validate_timestamp_float(self):
        """Test validating float timestamp"""
        timestamp = 1705276800.5

        result = Validators.validate_timestamp(timestamp)
        # Should convert to int and milliseconds
        assert isinstance(result, int)

    def test_validate_timestamp_before_2000(self):
        """Test validating timestamp before 2000"""
        # 1999-01-01 00:00:00 UTC
        timestamp = 915148800

        with pytest.raises(DataValidationError, match="must be after 2000-01-01"):
            Validators.validate_timestamp(timestamp)

    def test_validate_timestamp_future(self):
        """Test validating future timestamp"""
        import datetime
        future = datetime.datetime.now() + datetime.timedelta(days=30)
        timestamp = int(future.timestamp())

        with pytest.raises(DataValidationError, match="cannot be in the future"):
            Validators.validate_timestamp(timestamp)

    def test_validate_timestamp_invalid_type(self):
        """Test validating with invalid type"""
        with pytest.raises(DataValidationError, match="must be a valid integer or float"):
            Validators.validate_timestamp("invalid")

    def test_validate_timestamp_custom_param_name(self):
        """Test validating with custom parameter name"""
        with pytest.raises(DataValidationError, match="custom_field must be a valid integer"):
            Validators.validate_timestamp("invalid", param_name="custom_field")


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test convenience validation functions"""

    def test_validate_symbol_convenience(self):
        """Test validate_symbol convenience function"""
        from tvDatafeed.validators import validate_symbol
        assert validate_symbol("BTCUSDT") == "BTCUSDT"

    def test_validate_exchange_convenience(self):
        """Test validate_exchange convenience function"""
        from tvDatafeed.validators import validate_exchange
        assert validate_exchange("BINANCE") == "BINANCE"

    def test_validate_n_bars_convenience(self):
        """Test validate_n_bars convenience function"""
        from tvDatafeed.validators import validate_n_bars
        assert validate_n_bars(100) == 100

    def test_validate_ohlc_convenience(self):
        """Test validate_ohlc convenience function"""
        from tvDatafeed.validators import validate_ohlc
        assert validate_ohlc(100, 105, 95, 102) is True


@pytest.mark.unit
class TestValidatorsEdgeCases:
    """Test edge cases for validators"""

    def test_validate_symbol_none(self):
        """Test validating None symbol"""
        with pytest.raises(DataValidationError, match="must be a non-empty string"):
            Validators.validate_symbol(None)

    def test_validate_symbol_non_string(self):
        """Test validating non-string symbol"""
        with pytest.raises(DataValidationError, match="must be a non-empty string"):
            Validators.validate_symbol(123)

    def test_validate_exchange_none(self):
        """Test validating None exchange"""
        with pytest.raises(DataValidationError, match="must be a non-empty string"):
            Validators.validate_exchange(None)

    def test_validate_exchange_non_string(self):
        """Test validating non-string exchange"""
        with pytest.raises(DataValidationError, match="must be a non-empty string"):
            Validators.validate_exchange(456)

    def test_validate_symbol_disallow_formatted(self):
        """Test validating symbol with allow_formatted=False"""
        # Should not allow colon in symbol when allow_formatted is False
        with pytest.raises(DataValidationError):
            Validators.validate_symbol("BINANCE:BTCUSDT", allow_formatted=False)

    def test_validate_n_bars_custom_max(self):
        """Test validating n_bars with custom max"""
        # Should pass with custom max
        assert Validators.validate_n_bars(100, max_bars=100) == 100

        # Should fail when exceeding custom max
        with pytest.raises(DataValidationError, match="cannot exceed 100"):
            Validators.validate_n_bars(101, max_bars=100)

    def test_validate_credentials_whitespace_only_username(self):
        """Test validating with whitespace-only username"""
        with pytest.raises(ConfigurationError, match="must be a non-empty string"):
            Validators.validate_credentials("   ", "pass")

    def test_validate_credentials_whitespace_only_password(self):
        """Test validating with whitespace-only password"""
        with pytest.raises(ConfigurationError, match="must be a non-empty string"):
            Validators.validate_credentials("user", "   ")

    def test_validate_ohlc_invalid_low_no_raise(self):
        """Test validating OHLC with invalid low without raising"""
        # Low > min(open, close) - this should return False when raise_on_error=False
        result = Validators.validate_ohlc(100, 105, 101, 102, raise_on_error=False)
        assert result is False
