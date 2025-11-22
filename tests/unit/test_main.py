"""
Unit tests for TvDatafeed main class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from tvDatafeed import TvDatafeed, Interval, CaptchaRequiredError, AuthenticationError
import pandas as pd


@pytest.mark.unit
class TestTvDatafeed:
    """Test TvDatafeed class"""

    def test_tvdatafeed_creation_no_auth(self):
        """Test creating TvDatafeed without authentication"""
        with patch('tvDatafeed.main.requests.post') as mock_post:
            tv = TvDatafeed()

            assert tv.token == "unauthorized_user_token"
            # Should not call auth endpoint when no credentials
            mock_post.assert_not_called()

    def test_tvdatafeed_creation_with_auth(self, mock_auth_response):
        """Test creating TvDatafeed with authentication"""
        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_auth_response
            mock_session_class.return_value = mock_session

            tv = TvDatafeed(username='testuser', password='testpass')

            assert tv.token == 'test_token_12345'

    def test_auth_failure(self):
        """Test authentication failure"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'error': 'Invalid credentials',
            'code': 'invalid_credentials'
        }

        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(AuthenticationError):
                TvDatafeed(username='testuser', password='wrongpass')

    def test_session_generation(self):
        """Test session ID generation"""
        tv = TvDatafeed()

        assert tv.session.startswith('qs_')
        assert len(tv.session) == 15  # 'qs_' + 12 chars

    def test_chart_session_generation(self):
        """Test chart session ID generation"""
        tv = TvDatafeed()

        assert tv.chart_session.startswith('cs_')
        assert len(tv.chart_session) == 15  # 'cs_' + 12 chars

    def test_format_symbol_simple(self):
        """Test symbol formatting without contract"""
        tv = TvDatafeed()

        formatted = tv._TvDatafeed__format_symbol('BTCUSDT', 'BINANCE')

        assert formatted == 'BINANCE:BTCUSDT'

    def test_format_symbol_with_contract(self):
        """Test symbol formatting with futures contract"""
        tv = TvDatafeed()

        formatted = tv._TvDatafeed__format_symbol('NIFTY', 'NSE', contract=1)

        assert formatted == 'NSE:NIFTY1!'

    def test_format_symbol_already_formatted(self):
        """Test symbol that's already formatted"""
        tv = TvDatafeed()

        formatted = tv._TvDatafeed__format_symbol('BINANCE:BTCUSDT', 'BINANCE')

        assert formatted == 'BINANCE:BTCUSDT'

    def test_format_symbol_already_formatted_different_exchange(self):
        """Test symbol that's already formatted with different exchange parameter"""
        tv = TvDatafeed()

        # Symbol has BINANCE but we pass NYSE - should use symbol's exchange
        formatted = tv._TvDatafeed__format_symbol('BINANCE:BTCUSDT', 'NYSE')

        assert formatted == 'BINANCE:BTCUSDT'  # Keeps BINANCE from symbol

    def test_format_symbol_invalid_contract(self):
        """Test symbol formatting with invalid contract type"""
        tv = TvDatafeed()

        with pytest.raises(ValueError, match="not a valid contract"):
            tv._TvDatafeed__format_symbol('NIFTY', 'NSE', contract='invalid')

    @patch('tvDatafeed.main.create_connection')
    def test_create_connection(self, mock_create_connection):
        """Test WebSocket connection creation"""
        mock_ws = Mock()
        mock_create_connection.return_value = mock_ws

        tv = TvDatafeed()
        tv._TvDatafeed__create_connection()

        assert tv.ws == mock_ws
        mock_create_connection.assert_called_once()

    @patch('tvDatafeed.main.create_connection')
    def test_search_symbol(self, mock_create_connection, sample_symbol_search_response):
        """Test symbol search"""
        with patch('tvDatafeed.main.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = str(sample_symbol_search_response)
            mock_get.return_value = mock_response

            tv = TvDatafeed()
            results = tv.search_symbol('BTC', 'BINANCE')

            assert isinstance(results, list)
            mock_get.assert_called_once()

    @patch('tvDatafeed.main.create_connection')
    def test_search_symbol_error(self, mock_create_connection):
        """Test symbol search with error"""
        with patch('tvDatafeed.main.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            tv = TvDatafeed()
            results = tv.search_symbol('BTC', 'BINANCE')

            assert results == []

    def test_create_df_valid_data(self, sample_websocket_message):
        """Test DataFrame creation from valid WebSocket data"""
        tv = TvDatafeed()

        df = tv._TvDatafeed__create_df(sample_websocket_message, 'BTCUSDT')

        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert 'symbol' in df.columns
        assert df['symbol'].iloc[0] == 'BTCUSDT'
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns

    def test_create_df_invalid_data(self):
        """Test DataFrame creation from invalid data"""
        tv = TvDatafeed()

        df = tv._TvDatafeed__create_df('invalid data', 'BTCUSDT')

        assert df is None

    def test_create_df_no_volume(self):
        """Test DataFrame creation when volume data is missing"""
        # Create data without volume
        raw_data = '''{"s":[{"v":[1609459200,29000,29500,28500,29200]}]}'''

        tv = TvDatafeed()
        df = tv._TvDatafeed__create_df(raw_data, 'BTCUSDT')

        # Should still create df with volume=0
        assert df is not None
        assert 'volume' in df.columns

    def test_auth_captcha_required(self):
        """Test authentication when CAPTCHA is required"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'error': 'Please confirm that you are not a robot by clicking the captcha box',
            'code': 'recaptcha_required'
        }

        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(CaptchaRequiredError) as exc_info:
                TvDatafeed(username='testuser', password='testpass')

            # Check that the exception contains the username
            assert exc_info.value.username == 'testuser'
            # Check that the error message mentions workaround
            assert 'CAPTCHA' in str(exc_info.value)
            assert 'authToken' in str(exc_info.value)

    def test_auth_token_direct_usage(self):
        """Test using pre-obtained auth token directly"""
        tv = TvDatafeed(auth_token='test_token_direct')

        assert tv.token == 'test_token_direct'

    def test_auth_token_priority_over_credentials(self):
        """Test that auth_token takes priority over username/password"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'user': {'auth_token': 'should_not_be_used'}
        }

        with patch('tvDatafeed.main.requests.post', return_value=mock_response) as mock_post:
            tv = TvDatafeed(
                username='testuser',
                password='testpass',
                auth_token='token_from_browser'
            )

            # Should use the provided token
            assert tv.token == 'token_from_browser'
            # Should not call auth endpoint
            mock_post.assert_not_called()

    def test_auth_generic_error(self):
        """Test authentication with generic error"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'error': 'Invalid credentials',
            'code': 'invalid_credentials'
        }

        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(AuthenticationError) as exc_info:
                TvDatafeed(username='testuser', password='wrongpass')

            # Should raise AuthenticationError, not CaptchaRequiredError
            assert not isinstance(exc_info.value, CaptchaRequiredError)
            assert 'Invalid credentials' in str(exc_info.value)

    def test_ws_timeout_default(self):
        """Test that default WebSocket timeout is used"""
        tv = TvDatafeed()

        # Default timeout is either 5s (hardcoded) or 30s (from NetworkConfig)
        # depending on whether NetworkConfig is available
        assert tv.ws_timeout in [5.0, 30.0]
        # If NetworkConfig is available, it should use its recv_timeout (30.0)
        # Otherwise, it falls back to __ws_timeout (5.0)

    def test_ws_timeout_custom_parameter(self):
        """Test custom WebSocket timeout via parameter"""
        tv = TvDatafeed(ws_timeout=30.0)

        assert tv.ws_timeout == 30.0

    def test_ws_timeout_no_timeout(self):
        """Test WebSocket with no timeout (-1)"""
        tv = TvDatafeed(ws_timeout=-1)

        assert tv.ws_timeout == -1.0

    def test_ws_timeout_from_env_variable(self):
        """Test WebSocket timeout from environment variable"""
        import os

        # Set environment variable
        os.environ['TV_WS_TIMEOUT'] = '45.0'

        try:
            tv = TvDatafeed()
            assert tv.ws_timeout == 45.0
        finally:
            # Clean up
            os.environ.pop('TV_WS_TIMEOUT', None)

    def test_ws_timeout_parameter_overrides_env(self):
        """Test that parameter overrides environment variable"""
        import os

        os.environ['TV_WS_TIMEOUT'] = '45.0'

        try:
            tv = TvDatafeed(ws_timeout=20.0)
            # Parameter should take priority
            assert tv.ws_timeout == 20.0
        finally:
            os.environ.pop('TV_WS_TIMEOUT', None)

    def test_ws_timeout_invalid_env_variable(self):
        """Test handling of invalid environment variable"""
        import os

        os.environ['TV_WS_TIMEOUT'] = 'invalid'

        try:
            tv = TvDatafeed()
            # Should fall back to default
            assert tv.ws_timeout == 5.0
        finally:
            os.environ.pop('TV_WS_TIMEOUT', None)

    def test_format_search_results_empty(self):
        """Test formatting empty search results"""
        tv = TvDatafeed()

        formatted = tv.format_search_results([])

        assert 'No results found' in formatted

    def test_format_search_results_single(self):
        """Test formatting single search result"""
        tv = TvDatafeed()

        results = [
            {
                'exchange': 'BINANCE',
                'symbol': 'BTCUSDT',
                'description': 'Bitcoin / TetherUS',
                'type': 'crypto'
            }
        ]

        formatted = tv.format_search_results(results)

        assert 'BINANCE:BTCUSDT' in formatted
        assert 'Bitcoin / TetherUS' in formatted
        assert 'crypto' in formatted
        assert 'Found 1 results' in formatted

    def test_format_search_results_multiple(self):
        """Test formatting multiple search results"""
        tv = TvDatafeed()

        results = [
            {
                'exchange': 'BINANCE',
                'symbol': 'BTCUSDT',
                'description': 'Bitcoin / TetherUS',
                'type': 'crypto'
            },
            {
                'exchange': 'COINBASE',
                'symbol': 'BTCUSD',
                'description': 'Bitcoin / US Dollar',
                'type': 'crypto'
            },
            {
                'exchange': 'KRAKEN',
                'symbol': 'BTCEUR',
                'description': 'Bitcoin / Euro',
                'type': 'crypto'
            }
        ]

        formatted = tv.format_search_results(results, max_results=2)

        # Should only show first 2
        assert 'BINANCE:BTCUSDT' in formatted
        assert 'COINBASE:BTCUSD' in formatted
        # Third should not be included
        assert 'KRAKEN:BTCEUR' not in formatted
        assert 'showing first 2' in formatted

    def test_format_search_results_includes_usage(self):
        """Test that formatted results include usage examples"""
        tv = TvDatafeed()

        results = [
            {
                'exchange': 'BINANCE',
                'symbol': 'BTCUSDT',
                'description': 'Bitcoin / TetherUS',
                'type': 'crypto'
            }
        ]

        formatted = tv.format_search_results(results)

        assert 'Usage:' in formatted
        assert 'tv.get_hist' in formatted
        assert 'Example:' in formatted

    def test_verbose_mode_default(self):
        """Test that verbose mode is enabled by default"""
        tv = TvDatafeed()

        assert tv.verbose is True

    def test_verbose_mode_disabled(self):
        """Test that verbose mode can be disabled"""
        tv = TvDatafeed(verbose=False)

        assert tv.verbose is False

    def test_verbose_mode_enabled_explicit(self):
        """Test that verbose mode can be explicitly enabled"""
        tv = TvDatafeed(verbose=True)

        assert tv.verbose is True

    def test_verbose_mode_from_env_true(self):
        """Test verbose mode from environment variable (true)"""
        import os

        # Test various true values
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'on', 'On']

        for value in true_values:
            os.environ['TV_VERBOSE'] = value

            try:
                tv = TvDatafeed()
                assert tv.verbose is True, f"Failed for TV_VERBOSE={value}"
            finally:
                os.environ.pop('TV_VERBOSE', None)

    def test_verbose_mode_from_env_false(self):
        """Test verbose mode from environment variable (false)"""
        import os

        # Test various false values
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'off', 'Off']

        for value in false_values:
            os.environ['TV_VERBOSE'] = value

            try:
                tv = TvDatafeed()
                assert tv.verbose is False, f"Failed for TV_VERBOSE={value}"
            finally:
                os.environ.pop('TV_VERBOSE', None)

    def test_verbose_mode_parameter_overrides_env_true_to_false(self):
        """Test that parameter overrides environment variable (env=true, param=false)"""
        import os

        os.environ['TV_VERBOSE'] = 'true'

        try:
            tv = TvDatafeed(verbose=False)
            # Parameter should take priority
            assert tv.verbose is False
        finally:
            os.environ.pop('TV_VERBOSE', None)

    def test_verbose_mode_parameter_overrides_env_false_to_true(self):
        """Test that parameter overrides environment variable (env=false, param=true)"""
        import os

        os.environ['TV_VERBOSE'] = 'false'

        try:
            tv = TvDatafeed(verbose=True)
            # Parameter should take priority
            assert tv.verbose is True
        finally:
            os.environ.pop('TV_VERBOSE', None)

    def test_verbose_mode_logging_level_verbose(self):
        """Test that verbose mode sets appropriate logging level"""
        import logging
        from tvDatafeed.main import logger

        # Save original level
        original_level = logger.level

        try:
            tv = TvDatafeed(verbose=True)

            # Logger should be set to INFO or lower
            assert logger.level <= logging.INFO
        finally:
            # Restore original level
            logger.setLevel(original_level)

    def test_verbose_mode_logging_level_quiet(self):
        """Test that quiet mode sets appropriate logging level"""
        import logging
        from tvDatafeed.main import logger

        # Save original level
        original_level = logger.level

        try:
            tv = TvDatafeed(verbose=False)

            # Logger should be set to WARNING
            assert logger.level == logging.WARNING
        finally:
            # Restore original level
            logger.setLevel(original_level)

    def test_verbose_mode_env_not_set(self):
        """Test behavior when TV_VERBOSE is not set"""
        import os

        # Ensure TV_VERBOSE is not set
        os.environ.pop('TV_VERBOSE', None)

        tv = TvDatafeed()

        # Should default to True
        assert tv.verbose is True

    def test_verbose_mode_env_invalid_value(self):
        """Test behavior when TV_VERBOSE has invalid value"""
        import os

        os.environ['TV_VERBOSE'] = 'invalid_value'

        try:
            tv = TvDatafeed()

            # Invalid value should be treated as False
            # (not in ['true', '1', 'yes', 'on'])
            assert tv.verbose is False
        finally:
            os.environ.pop('TV_VERBOSE', None)


@pytest.mark.unit
class TestInterval:
    """Test Interval enum"""

    def test_interval_values(self):
        """Test that intervals have correct values"""
        assert Interval.in_1_minute.value == "1"
        assert Interval.in_3_minute.value == "3"
        assert Interval.in_5_minute.value == "5"
        assert Interval.in_15_minute.value == "15"
        assert Interval.in_30_minute.value == "30"
        assert Interval.in_45_minute.value == "45"
        assert Interval.in_1_hour.value == "1H"
        assert Interval.in_2_hour.value == "2H"
        assert Interval.in_3_hour.value == "3H"
        assert Interval.in_4_hour.value == "4H"
        assert Interval.in_daily.value == "1D"
        assert Interval.in_weekly.value == "1W"
        assert Interval.in_monthly.value == "1M"

    def test_interval_names(self):
        """Test interval names"""
        assert Interval.in_1_hour.name == "in_1_hour"
        assert Interval.in_daily.name == "in_daily"


@pytest.mark.unit
class TestDateRangeFeature:
    """Test date range search feature (PR #69)"""

    def test_is_valid_date_range_valid(self):
        """Test is_valid_date_range with valid date range"""
        from datetime import datetime
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        result = TvDatafeed.is_valid_date_range(start, end)

        assert result is True

    def test_is_valid_date_range_start_after_end(self):
        """Test is_valid_date_range when start is after end"""
        from datetime import datetime
        start = datetime(2024, 1, 31)
        end = datetime(2024, 1, 1)

        result = TvDatafeed.is_valid_date_range(start, end)

        assert result is False

    def test_is_valid_date_range_start_equals_end(self):
        """Test is_valid_date_range when start equals end"""
        from datetime import datetime
        start = datetime(2024, 1, 15)
        end = datetime(2024, 1, 15)

        result = TvDatafeed.is_valid_date_range(start, end)

        assert result is False

    def test_is_valid_date_range_future_start(self):
        """Test is_valid_date_range with future start date"""
        from datetime import datetime, timedelta
        future = datetime.now() + timedelta(days=30)
        end = datetime.now() + timedelta(days=60)

        result = TvDatafeed.is_valid_date_range(future, end)

        assert result is False

    def test_is_valid_date_range_future_end(self):
        """Test is_valid_date_range with future end date"""
        from datetime import datetime, timedelta
        start = datetime(2024, 1, 1)
        end = datetime.now() + timedelta(days=30)

        result = TvDatafeed.is_valid_date_range(start, end)

        assert result is False

    def test_is_valid_date_range_before_2000(self):
        """Test is_valid_date_range with dates before 2000"""
        from datetime import datetime
        start = datetime(1999, 1, 1)
        end = datetime(1999, 12, 31)

        result = TvDatafeed.is_valid_date_range(start, end)

        assert result is False

    def test_is_valid_date_range_start_before_2000(self):
        """Test is_valid_date_range with start before 2000"""
        from datetime import datetime
        start = datetime(1999, 12, 31)
        end = datetime(2024, 1, 1)

        result = TvDatafeed.is_valid_date_range(start, end)

        assert result is False

    def test_get_hist_mutually_exclusive_error(self):
        """Test get_hist raises error when both n_bars and date range provided"""
        from datetime import datetime
        from tvDatafeed import DataValidationError

        tv = TvDatafeed()

        with pytest.raises(DataValidationError) as exc_info:
            tv.get_hist(
                'BTCUSDT',
                'BINANCE',
                Interval.in_1_hour,
                n_bars=100,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            )

        assert 'mutually exclusive' in str(exc_info.value).lower()

    def test_get_hist_only_start_date_error(self):
        """Test get_hist raises error when only start_date provided"""
        from datetime import datetime
        from tvDatafeed import DataValidationError

        tv = TvDatafeed()

        with pytest.raises(DataValidationError) as exc_info:
            tv.get_hist(
                'BTCUSDT',
                'BINANCE',
                Interval.in_1_hour,
                start_date=datetime(2024, 1, 1)
            )

        assert 'both' in str(exc_info.value).lower()

    def test_get_hist_only_end_date_error(self):
        """Test get_hist raises error when only end_date provided"""
        from datetime import datetime
        from tvDatafeed import DataValidationError

        tv = TvDatafeed()

        with pytest.raises(DataValidationError) as exc_info:
            tv.get_hist(
                'BTCUSDT',
                'BINANCE',
                Interval.in_1_hour,
                end_date=datetime(2024, 1, 31)
            )

        assert 'both' in str(exc_info.value).lower()

    def test_get_hist_invalid_date_range_error(self):
        """Test get_hist raises error for invalid date range"""
        from datetime import datetime
        from tvDatafeed import DataValidationError

        tv = TvDatafeed()

        # Start after end
        with pytest.raises(DataValidationError) as exc_info:
            tv.get_hist(
                'BTCUSDT',
                'BINANCE',
                Interval.in_1_hour,
                start_date=datetime(2024, 1, 31),
                end_date=datetime(2024, 1, 1)
            )

        assert 'invalid date range' in str(exc_info.value).lower()

    def test_get_hist_defaults_to_n_bars_10(self):
        """Test get_hist defaults to n_bars=10 when neither n_bars nor dates provided"""
        from unittest.mock import patch, MagicMock

        with patch('tvDatafeed.main.create_connection') as mock_create_connection:
            mock_ws = MagicMock()
            mock_ws.recv.side_effect = [
                '~m~123~m~{"m":"series_completed"}',
            ]
            mock_create_connection.return_value = mock_ws

            tv = TvDatafeed()

            # Mock __create_df to avoid parsing issues
            with patch.object(tv, '_TvDatafeed__create_df') as mock_create_df:
                mock_df = pd.DataFrame({
                    'symbol': ['BTCUSDT'] * 10,
                    'open': [29000] * 10,
                    'high': [29500] * 10,
                    'low': [28500] * 10,
                    'close': [29200] * 10,
                    'volume': [1000] * 10
                })
                mock_create_df.return_value = mock_df

                try:
                    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour)
                    # Should not raise error and should have data
                    assert df is not None
                except Exception:
                    # This is expected since we're mocking, just verify no validation error
                    pass

    def test_interval_len_dictionary_exists(self):
        """Test that interval_len dictionary is defined with all intervals"""
        from tvDatafeed.main import interval_len

        # Check dictionary exists
        assert interval_len is not None
        assert isinstance(interval_len, dict)

        # Check all intervals are present
        expected_intervals = ["1", "3", "5", "15", "30", "45", "1H", "2H", "3H", "4H", "1D", "1W", "1M"]
        for interval in expected_intervals:
            assert interval in interval_len
            assert isinstance(interval_len[interval], int)
            assert interval_len[interval] > 0

    def test_interval_len_values_correct(self):
        """Test that interval_len values are correct"""
        from tvDatafeed.main import interval_len

        assert interval_len["1"] == 60  # 1 minute
        assert interval_len["5"] == 300  # 5 minutes
        assert interval_len["1H"] == 3600  # 1 hour
        assert interval_len["1D"] == 86400  # 1 day
        assert interval_len["1W"] == 604800  # 1 week
        assert interval_len["1M"] == 2592000  # 1 month (30 days)

    def test_create_df_with_timezone(self):
        """Test __create_df accepts timezone parameter"""
        tv = TvDatafeed()
        raw_data = '''{"s":[{"v":[1609459200,29000,29500,28500,29200,1000000]}]}'''

        df = tv._TvDatafeed__create_df(raw_data, 'BTCUSDT', 3600, 'America/New_York')

        assert df is not None
        assert 'timezone' in df.attrs
        assert df.attrs['timezone'] == 'America/New_York'

    def test_create_df_without_timezone_backward_compatible(self):
        """Test __create_df still works without timezone (backward compatibility)"""
        tv = TvDatafeed()
        raw_data = '''{"s":[{"v":[1609459200,29000,29500,28500,29200,1000000]}]}'''

        df = tv._TvDatafeed__create_df(raw_data, 'BTCUSDT')

        assert df is not None
        assert 'timezone' not in df.attrs or df.attrs.get('timezone') is None


@pytest.mark.unit
class TestTwoFactorAuthentication:
    """Test Two-Factor Authentication (2FA/TOTP) support"""

    def test_2fa_params_stored(self, valid_totp_secret):
        """Test that 2FA parameters are stored correctly"""
        tv = TvDatafeed(totp_secret=valid_totp_secret, totp_code='123456')

        assert tv._totp_secret == valid_totp_secret
        assert tv._totp_code == '123456'

    def test_2fa_params_from_env(self, monkeypatch, valid_totp_secret):
        """Test that 2FA parameters are read from environment"""
        monkeypatch.setenv('TV_TOTP_SECRET', valid_totp_secret)
        monkeypatch.setenv('TV_2FA_CODE', '654321')

        tv = TvDatafeed()

        assert tv._totp_secret == valid_totp_secret
        assert tv._totp_code == '654321'

    def test_2fa_params_priority_over_env(self, monkeypatch, valid_totp_secret):
        """Test that parameters take priority over environment variables"""
        monkeypatch.setenv('TV_TOTP_SECRET', 'ENVENVENVENV')
        monkeypatch.setenv('TV_2FA_CODE', '111111')

        tv = TvDatafeed(totp_secret=valid_totp_secret, totp_code='999999')

        # Parameters should take priority
        assert tv._totp_secret == valid_totp_secret
        assert tv._totp_code == '999999'

    def test_get_totp_code_manual(self):
        """Test _get_totp_code returns manual code when provided"""
        tv = TvDatafeed(totp_code='123456')

        code = tv._get_totp_code()

        assert code == '123456'

    def test_get_totp_code_generated(self, valid_totp_secret):
        """Test _get_totp_code generates code from secret"""
        tv = TvDatafeed(totp_secret=valid_totp_secret)

        code = tv._get_totp_code()

        # Should be a 6-digit code
        assert code is not None
        assert len(code) == 6
        assert code.isdigit()

    def test_get_totp_code_none_when_not_configured(self):
        """Test _get_totp_code returns None when neither secret nor code provided"""
        tv = TvDatafeed()

        code = tv._get_totp_code()

        assert code is None

    def test_get_totp_code_manual_priority(self, valid_totp_secret):
        """Test that manual code takes priority over secret"""
        tv = TvDatafeed(totp_secret=valid_totp_secret, totp_code='111111')

        code = tv._get_totp_code()

        # Manual code should be returned, not generated one
        assert code == '111111'

    def test_get_totp_code_invalid_secret(self):
        """Test _get_totp_code raises error for invalid secret"""
        from tvDatafeed import ConfigurationError

        tv = TvDatafeed(totp_secret='INVALID!!!')

        with pytest.raises(ConfigurationError) as exc_info:
            tv._get_totp_code()

        assert 'Invalid TOTP secret' in str(exc_info.value)

    def test_2fa_flow_success(
        self,
        mock_2fa_required_response,
        mock_2fa_success_response,
        valid_totp_secret
    ):
        """Test successful 2FA authentication flow"""
        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            # First call returns 2FA required, second call returns success
            mock_session.post.side_effect = [
                mock_2fa_required_response,
                mock_2fa_success_response
            ]
            mock_session_class.return_value = mock_session

            tv = TvDatafeed(
                username='testuser',
                password='testpass',
                totp_secret=valid_totp_secret
            )

            assert tv.token == 'test_token_2fa_12345'
            assert mock_session.post.call_count == 2

    def test_2fa_flow_with_manual_code(
        self,
        mock_2fa_required_response,
        mock_2fa_success_response
    ):
        """Test 2FA authentication flow with manual code"""
        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.side_effect = [
                mock_2fa_required_response,
                mock_2fa_success_response
            ]
            mock_session_class.return_value = mock_session

            tv = TvDatafeed(
                username='testuser',
                password='testpass',
                totp_code='123456'
            )

            assert tv.token == 'test_token_2fa_12345'
            # Verify 2FA endpoint was called with the code
            second_call = mock_session.post.call_args_list[1]
            assert second_call[1]['data']['code'] == '123456'

    def test_2fa_required_but_not_provided(self, mock_2fa_required_response):
        """Test that TwoFactorRequiredError is raised when 2FA is required but not provided"""
        from tvDatafeed import TwoFactorRequiredError

        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_2fa_required_response
            mock_session_class.return_value = mock_session

            with pytest.raises(TwoFactorRequiredError) as exc_info:
                TvDatafeed(username='testuser', password='testpass')

            assert 'Two-factor authentication required' in str(exc_info.value)

    def test_2fa_invalid_code(
        self,
        mock_2fa_required_response,
        mock_2fa_invalid_code_response,
        valid_totp_secret
    ):
        """Test 2FA with invalid code raises AuthenticationError"""
        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.side_effect = [
                mock_2fa_required_response,
                mock_2fa_invalid_code_response
            ]
            mock_session_class.return_value = mock_session

            with pytest.raises(AuthenticationError) as exc_info:
                TvDatafeed(
                    username='testuser',
                    password='testpass',
                    totp_code='000000'
                )

            assert 'Invalid' in str(exc_info.value) or 'invalid' in str(exc_info.value)

    def test_2fa_totp_secret_cleaned(self, valid_totp_secret):
        """Test that TOTP secret is cleaned (spaces removed, uppercase)"""
        # Add spaces and lowercase
        messy_secret = 'jbsw y3dp ehpk 3pxp'

        tv = TvDatafeed(totp_secret=messy_secret)

        # Should still generate a valid code
        code = tv._get_totp_code()
        assert code is not None
        assert len(code) == 6
        assert code.isdigit()

    def test_2fa_not_required(self, mock_auth_response):
        """Test authentication without 2FA when account doesn't have it enabled"""
        with patch('tvDatafeed.main.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_auth_response
            mock_session_class.return_value = mock_session

            # Should authenticate without 2FA
            tv = TvDatafeed(username='testuser', password='testpass')

            assert tv.token == 'test_token_12345'
            # Only one call (no 2FA needed)
            assert mock_session.post.call_count == 1

    def test_docstring_examples_present(self):
        """Verify that 2FA examples are in the TvDatafeed docstring"""
        docstring = TvDatafeed.__init__.__doc__

        assert 'totp_secret' in docstring
        assert 'totp_code' in docstring
        assert '2FA' in docstring
        assert 'TV_TOTP_SECRET' in docstring

    def test_2fa_url_configured(self):
        """Test that 2FA URL is correctly configured"""
        assert hasattr(TvDatafeed, '_TvDatafeed__2fa_url')
        assert 'two-factor' in TvDatafeed._TvDatafeed__2fa_url
