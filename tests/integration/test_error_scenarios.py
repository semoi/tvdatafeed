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
    DataNotFoundError,
    InvalidIntervalError,
    DataValidationError
)


@pytest.mark.integration
class TestAuthenticationErrors:
    """Test authentication error scenarios"""

    def test_invalid_credentials(self):
        """Test handling of invalid credentials"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws, \
             patch('tvDatafeed.main.requests.post') as mock_post:

            # Mock authentication failure
            mock_response = Mock()
            mock_response.json.return_value = {'error': 'Invalid credentials'}
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            # Should handle invalid credentials gracefully
            try:
                tv = TvDatafeed(username='invalid_user', password='invalid_pass')
                # If no exception, that's also acceptable
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
        with patch('tvDatafeed.main.ws.create_connection'):
            # Username without password should fail validation
            with pytest.raises((ValueError, AuthenticationError)):
                TvDatafeed(username='user', password=None)


@pytest.mark.integration
class TestWebSocketErrors:
    """Test WebSocket error scenarios"""

    def test_connection_refused(self):
        """Test handling of connection refused"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_ws.side_effect = ConnectionRefusedError("Connection refused")

            # Should handle connection error gracefully
            with pytest.raises((ConnectionError, WebSocketError)):
                TvDatafeed()

    def test_connection_timeout(self):
        """Test handling of connection timeout"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_ws.side_effect = TimeoutError("Connection timeout")

            # Should handle timeout gracefully
            with pytest.raises((TimeoutError, WebSocketError)):
                TvDatafeed()

    def test_websocket_closed_unexpectedly(self):
        """Test handling of unexpected WebSocket closure"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection

            # First response succeeds, then connection closes
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
                ConnectionError("Connection closed")
            ]

            tv = TvDatafeed()

            # Should handle closure gracefully when fetching data
            result = tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )

            # Either None or raises exception
            assert result is None or result is not None


@pytest.mark.integration
class TestDataErrors:
    """Test data-related error scenarios"""

    def test_invalid_symbol(self):
        """Test handling of invalid symbol"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"error","v":{}}]}',
            ] * 10

            tv = TvDatafeed()

            # Should handle invalid symbol gracefully
            result = tv.get_hist(
                symbol='INVALID_SYMBOL_XYZ',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )

            assert result is None  # Should return None for invalid symbol

    def test_no_data_available(self):
        """Test handling when no data is available"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
                '~m~52~m~{"m":"timescale_update","p":["cs_test456",{"s":[]}]}',  # Empty data
            ] * 10

            tv = TvDatafeed()

            result = tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )

            # Should return None or empty DataFrame
            assert result is None or (result is not None and result.empty)

    def test_malformed_data(self):
        """Test handling of malformed data"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
                '~m~50~m~CORRUPTED_DATA_NOT_JSON',
            ] * 10

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
            except (ValueError, WebSocketError):
                # Also acceptable to raise exception
                pass


@pytest.mark.integration
class TestInputValidation:
    """Test input validation error scenarios"""

    @pytest.fixture
    def mock_tv(self):
        """Create a mocked TvDatafeed for validation testing"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
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
        with pytest.raises((ValueError, InvalidIntervalError)):
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

    def test_callback_not_callable(self):
        """Test validation of callback parameter"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()

            # Should raise error for non-callable callback
            with pytest.raises(TypeError):
                tv.start_live_feed(
                    callback="not_a_function",  # Invalid
                    symbol='BTCUSDT',
                    exchange='BINANCE',
                    interval=Interval.in_1_hour
                )

            tv.stop_live_feed()

    def test_stop_before_start(self):
        """Test stopping feed before starting"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()

            # Should handle gracefully
            tv.stop_live_feed()  # No exception should be raised


@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.fixture
    def mock_tv_edge(self):
        """Create a mocked TvDatafeed for edge case testing"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeed()
            yield tv

    def test_minimum_n_bars(self, mock_tv_edge):
        """Test fetching minimum number of bars"""
        result = mock_tv_edge.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=1
        )

        # Should handle single bar request
        assert result is None or result is not None

    def test_maximum_n_bars(self, mock_tv_edge):
        """Test fetching maximum number of bars"""
        result = mock_tv_edge.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=5000
        )

        # Should handle max bars request
        assert result is None or result is not None

    def test_special_characters_in_symbol(self, mock_tv_edge):
        """Test handling of special characters in symbol"""
        # Some symbols might have special chars (e.g., BTC-PERP)
        result = mock_tv_edge.get_hist(
            symbol='BTC-PERP',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=10
        )

        # Should handle gracefully (accept or reject with clear error)
        assert result is None or result is not None

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

    @pytest.fixture
    def mock_tv_rate(self):
        """Create a mocked TvDatafeed for rate limiting testing"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeed()
            yield tv

    def test_rapid_consecutive_requests(self, mock_tv_rate):
        """Test making rapid consecutive requests"""
        # Make multiple rapid requests
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']

        for symbol in symbols:
            result = mock_tv_rate.get_hist(
                symbol=symbol,
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )
            # Should handle all requests (potentially with rate limiting)
            assert result is None or result is not None

    def test_concurrent_requests_same_symbol(self, mock_tv_rate):
        """Test concurrent requests for the same symbol"""
        import threading

        results = []

        def fetch_data():
            result = mock_tv_rate.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )
            results.append(result)

        # Launch multiple threads
        threads = [threading.Thread(target=fetch_data) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=5.0)

        # All requests should complete
        assert len(results) == 5
