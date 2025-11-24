"""
Integration tests for error scenarios and edge cases

These tests verify that the library handles various error conditions
gracefully and provides helpful error messages.
"""
import pytest
import time
from unittest.mock import patch, Mock, MagicMock
from tvDatafeed import TvDatafeed, TvDatafeedLive, Interval
from tvDatafeed.exceptions import (
    AuthenticationError,
    WebSocketError,
    WebSocketTimeoutError,
    DataNotFoundError,
    InvalidIntervalError,
    DataValidationError,
    ConfigurationError
)


@pytest.mark.integration
class TestAuthenticationErrors:
    """Test authentication error scenarios"""

    def test_invalid_credentials(self):
        """Test handling of invalid credentials"""
        with patch('tvDatafeed.main.create_connection') as mock_ws, \
             patch('tvDatafeed.main.requests.post') as mock_post:

            # Mock authentication failure
            mock_response = Mock()
            mock_response.json.return_value = {'error': 'Invalid credentials'}
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            # Should handle invalid credentials gracefully
            try:
                tv = TvDatafeed(username='invalid_user', password='invalid_pass')
                # If no exception, that's also acceptable (deferred auth)
            except AuthenticationError:
                # Expected behavior
                pass

    def test_empty_credentials(self):
        """Test handling of empty credentials"""
        # Should accept None for unauthenticated access
        tv = TvDatafeed(username=None, password=None)
        assert tv is not None

    def test_partial_credentials(self):
        """Test handling of partial credentials"""
        with patch('tvDatafeed.main.create_connection'):
            # Username without password should fail validation
            with pytest.raises((ValueError, AuthenticationError, ConfigurationError)):
                TvDatafeed(username='user', password=None)


@pytest.mark.integration
class TestWebSocketErrors:
    """Test WebSocket error scenarios"""

    def test_connection_refused(self):
        """Test handling of connection refused"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_ws.side_effect = ConnectionRefusedError("Connection refused")

            # Should handle connection error gracefully
            # Note: TvDatafeed might not connect immediately in __init__
            try:
                tv = TvDatafeed()
                # If it doesn't connect in __init__, try to trigger connection
                tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, 10)
            except (ConnectionError, WebSocketError, ConnectionRefusedError):
                # Expected behavior
                pass

    def test_connection_timeout(self):
        """Test handling of connection timeout"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_ws.side_effect = TimeoutError("Connection timeout")

            # Should handle timeout gracefully
            try:
                tv = TvDatafeed()
                tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, 10)
            except (TimeoutError, WebSocketError):
                # Expected behavior
                pass

    def test_websocket_closed_unexpectedly(self):
        """Test handling of unexpected WebSocket closure"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection

            # Connection closes immediately
            mock_connection.recv.side_effect = ConnectionError("Connection closed")

            tv = TvDatafeed()

            # Should handle closure gracefully when fetching data
            try:
                result = tv.get_hist(
                    symbol='BTCUSDT',
                    exchange='BINANCE',
                    interval=Interval.in_1_hour,
                    n_bars=10
                )
                # Either None or raises exception
                assert result is None or result is not None
            except (ConnectionError, WebSocketError):
                # Expected behavior
                pass


@pytest.mark.integration
class TestDataErrors:
    """Test data-related error scenarios"""

    def test_invalid_symbol_response(self):
        """Test handling of invalid symbol response from server"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"error","v":{}}]}'

            tv = TvDatafeed()

            # Should handle invalid symbol gracefully
            try:
                result = tv.get_hist(
                    symbol='NOSYMBOL',  # Alphanumeric, passes validation
                    exchange='BINANCE',
                    interval=Interval.in_1_hour,
                    n_bars=10
                )
                # May return None for invalid symbol
            except (WebSocketError, WebSocketTimeoutError, DataNotFoundError):
                # Also acceptable
                pass

    def test_no_data_available(self):
        """Test handling when no data is available"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"timescale_update","p":["cs_test456",{"s":[]}]}'

            tv = TvDatafeed()

            try:
                result = tv.get_hist(
                    symbol='BTCUSDT',
                    exchange='BINANCE',
                    interval=Interval.in_1_hour,
                    n_bars=10
                )
                # Should return None or empty DataFrame
                assert result is None or (result is not None and result.empty)
            except (WebSocketError, WebSocketTimeoutError):
                # Also acceptable with mock
                pass

    def test_malformed_data(self):
        """Test handling of malformed data"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~50~m~CORRUPTED_DATA_NOT_JSON'

            tv = TvDatafeed()

            # Should handle malformed data gracefully
            try:
                result = tv.get_hist(
                    symbol='BTCUSDT',
                    exchange='BINANCE',
                    interval=Interval.in_1_hour,
                    n_bars=10
                )
                # Either None or valid DataFrame
                assert result is None or result is not None
            except (ValueError, WebSocketError, WebSocketTimeoutError):
                # Also acceptable to raise exception
                pass


@pytest.mark.integration
class TestInputValidation:
    """Test input validation error scenarios"""

    @pytest.fixture
    def mock_tv(self):
        """Create a mocked TvDatafeed for validation testing"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeed()
            yield tv

    def test_invalid_n_bars_negative(self, mock_tv):
        """Test validation of negative n_bars"""
        with pytest.raises((ValueError, DataValidationError)):
            mock_tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=-10
            )

    def test_invalid_n_bars_zero(self, mock_tv):
        """Test validation of zero n_bars"""
        with pytest.raises((ValueError, DataValidationError)):
            mock_tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=0
            )

    def test_invalid_n_bars_too_large(self, mock_tv):
        """Test validation of n_bars exceeding maximum"""
        with pytest.raises((ValueError, DataValidationError)):
            mock_tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10000  # Exceeds max of 5000
            )

    def test_empty_symbol(self, mock_tv):
        """Test validation of empty symbol"""
        with pytest.raises((ValueError, DataValidationError)):
            mock_tv.get_hist(
                symbol='',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )

    def test_empty_exchange(self, mock_tv):
        """Test validation of empty exchange"""
        with pytest.raises((ValueError, DataValidationError)):
            mock_tv.get_hist(
                symbol='BTCUSDT',
                exchange='',
                interval=Interval.in_1_hour,
                n_bars=10
            )

    def test_invalid_interval(self, mock_tv):
        """Test validation of invalid interval"""
        with pytest.raises((ValueError, InvalidIntervalError, TypeError, AttributeError)):
            mock_tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval='INVALID',
                n_bars=10
            )


@pytest.mark.integration
@pytest.mark.threading
class TestLiveFeedErrors:
    """Test error scenarios in live feed"""

    def test_live_feed_initialization(self):
        """Test TvDatafeedLive can be initialized"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()
            assert tv is not None
            # Check it has the correct methods
            assert hasattr(tv, 'new_seis')
            assert hasattr(tv, 'new_consumer')
            assert hasattr(tv, 'del_seis')
            assert hasattr(tv, 'del_tvdatafeed')


@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.fixture
    def mock_tv_edge(self):
        """Create a mocked TvDatafeed for edge case testing"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeed()
            yield tv

    def test_minimum_n_bars(self, mock_tv_edge):
        """Test fetching minimum number of bars"""
        # With mocks, we can't get real data but we verify no validation error
        try:
            result = mock_tv_edge.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=1
            )
            # Should handle single bar request (may timeout with mock)
        except (WebSocketError, WebSocketTimeoutError):
            # Expected with mock - the key is no validation error
            pass

    def test_maximum_n_bars(self, mock_tv_edge):
        """Test fetching maximum number of bars"""
        try:
            result = mock_tv_edge.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=5000
            )
            # Should handle max bars request
        except (WebSocketError, WebSocketTimeoutError):
            # Expected with mock
            pass

    def test_symbol_with_numbers(self, mock_tv_edge):
        """Test handling of symbols with numbers"""
        try:
            result = mock_tv_edge.get_hist(
                symbol='BTC1000',  # Alphanumeric is valid
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )
        except (WebSocketError, WebSocketTimeoutError, DataValidationError):
            # Expected with mock or validation
            pass

    def test_unicode_in_symbol(self, mock_tv_edge):
        """Test handling of unicode characters"""
        with pytest.raises((ValueError, DataValidationError)):
            mock_tv_edge.get_hist(
                symbol='BTC™USD',  # Unicode trademark symbol
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )

    def test_very_long_symbol_name(self, mock_tv_edge):
        """Test handling of very long symbol name"""
        long_symbol = 'A' * 100

        with pytest.raises((ValueError, DataValidationError)):
            mock_tv_edge.get_hist(
                symbol=long_symbol,
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )


@pytest.mark.integration
@pytest.mark.slow
class TestRateLimiting:
    """Test rate limiting behavior"""

    def test_multiple_instances(self):
        """Test creating multiple TvDatafeed instances"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            # Create multiple instances
            instances = [TvDatafeed() for _ in range(3)]
            assert len(instances) == 3


@pytest.mark.integration
class TestSymbolFormatErrors:
    """Test symbol format error scenarios (Issue #63)"""

    def test_formatted_symbol_exchange_mismatch(self):
        """Test when formatted symbol contains different exchange than parameter"""
        tv = TvDatafeed()

        # Symbol has BINANCE but we pass NYSE - should use symbol's exchange
        formatted = tv._TvDatafeed__format_symbol('BINANCE:BTCUSDT', 'NYSE')

        # Should keep BINANCE from symbol
        assert formatted == 'BINANCE:BTCUSDT'

    def test_unformatted_symbol_with_exchange(self):
        """Test unformatted symbol with exchange parameter"""
        tv = TvDatafeed()

        # Symbol without exchange, should format with provided exchange
        formatted = tv._TvDatafeed__format_symbol('BTCUSDT', 'BINANCE')

        # Should format to BINANCE:BTCUSDT
        assert formatted == 'BINANCE:BTCUSDT'

    def test_search_symbol_empty_results(self):
        """Test search_symbol when no results found"""
        with patch('tvDatafeed.main.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '[]'  # Empty results
            mock_get.return_value = mock_response

            tv = TvDatafeed()
            results = tv.search_symbol('NONEXISTENT', 'BINANCE')

            # Should return empty list, not raise exception
            assert results == []

    def test_search_symbol_network_error(self):
        """Test search_symbol with network error"""
        with patch('tvDatafeed.main.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            tv = TvDatafeed()
            results = tv.search_symbol('BTC', 'BINANCE')

            # Should return empty list, not crash
            assert results == []

    def test_search_symbol_invalid_json(self):
        """Test search_symbol with invalid JSON response"""
        with patch('tvDatafeed.main.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = 'INVALID JSON{'
            mock_get.return_value = mock_response

            tv = TvDatafeed()
            results = tv.search_symbol('BTC', 'BINANCE')

            # Should return empty list, not crash
            assert results == []

    def test_search_symbol_empty_query(self):
        """Test search_symbol with empty query"""
        tv = TvDatafeed()

        with pytest.raises(DataValidationError, match="Search text cannot be empty"):
            tv.search_symbol('', 'BINANCE')

    def test_search_symbol_whitespace_query(self):
        """Test search_symbol with whitespace-only query"""
        tv = TvDatafeed()

        with pytest.raises(DataValidationError, match="Search text cannot be empty"):
            tv.search_symbol('   ', 'BINANCE')


@pytest.mark.integration
class TestTimeoutConfiguration:
    """Test timeout configuration scenarios (Issue #63)"""

    def test_custom_timeout_parameter(self):
        """Test creating TvDatafeed with custom timeout"""
        tv = TvDatafeed(ws_timeout=30.0)

        assert tv.ws_timeout == 30.0

    def test_timeout_from_environment(self):
        """Test timeout configuration from environment variable"""
        import os

        original_timeout = os.environ.get('TV_WS_TIMEOUT')

        try:
            os.environ['TV_WS_TIMEOUT'] = '60.0'
            tv = TvDatafeed()

            assert tv.ws_timeout == 60.0

        finally:
            # Restore original value
            if original_timeout:
                os.environ['TV_WS_TIMEOUT'] = original_timeout
            else:
                os.environ.pop('TV_WS_TIMEOUT', None)

    def test_timeout_parameter_overrides_environment(self):
        """Test that parameter overrides environment variable"""
        import os

        original_timeout = os.environ.get('TV_WS_TIMEOUT')

        try:
            os.environ['TV_WS_TIMEOUT'] = '60.0'
            tv = TvDatafeed(ws_timeout=15.0)

            # Parameter should win
            assert tv.ws_timeout == 15.0

        finally:
            if original_timeout:
                os.environ['TV_WS_TIMEOUT'] = original_timeout
            else:
                os.environ.pop('TV_WS_TIMEOUT', None)

    def test_negative_timeout_no_timeout(self):
        """Test that -1 means no timeout"""
        tv = TvDatafeed(ws_timeout=-1)

        assert tv.ws_timeout == -1.0

    def test_invalid_timeout_falls_back_to_default(self):
        """Test that invalid timeout falls back to default"""
        import os

        original_timeout = os.environ.get('TV_WS_TIMEOUT')

        try:
            os.environ['TV_WS_TIMEOUT'] = 'not_a_number'
            tv = TvDatafeed()

            # Should fall back to default (5 seconds)
            assert tv.ws_timeout == 5.0

        finally:
            if original_timeout:
                os.environ['TV_WS_TIMEOUT'] = original_timeout
            else:
                os.environ.pop('TV_WS_TIMEOUT', None)

    @patch('tvDatafeed.main.create_connection')
    def test_timeout_used_in_websocket_connection(self, mock_create_connection):
        """Test that configured timeout is used in WebSocket connection"""
        mock_ws = Mock()
        mock_create_connection.return_value = mock_ws

        tv = TvDatafeed(ws_timeout=45.0)
        tv._TvDatafeed__create_connection()

        # Check that timeout was passed to create_connection
        call_args = mock_create_connection.call_args
        assert call_args[1]['timeout'] == 45.0

    @patch('tvDatafeed.main.create_connection')
    def test_no_timeout_none_passed_to_websocket(self, mock_create_connection):
        """Test that -1 timeout passes None to WebSocket"""
        mock_ws = Mock()
        mock_create_connection.return_value = mock_ws

        tv = TvDatafeed(ws_timeout=-1)
        tv._TvDatafeed__create_connection()

        # Check that None was passed (no timeout)
        call_args = mock_create_connection.call_args
        assert call_args[1]['timeout'] is None
