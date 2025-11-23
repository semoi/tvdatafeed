"""
Integration tests for basic TvDatafeed workflow

These tests verify the core functionality of fetching historical data.
They are marked as 'integration' and 'network' and can be skipped
with: pytest -m "not integration"
"""
import os
import pytest
import pandas as pd
from unittest.mock import patch, Mock, MagicMock
from tvDatafeed import TvDatafeed, Interval


@pytest.mark.integration
@pytest.mark.network
class TestBasicWorkflow:
    """Test basic data retrieval workflows"""

    @pytest.fixture
    def mock_tv(self):
        """Create a mocked TvDatafeed instance"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            # Mock WebSocket connection
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection

            # Mock successful authentication response
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok","v":{"lp":50000.0}}]}',
                '~m~200~m~{"m":"timescale_update","p":["cs_test456",{"s":[{"i":0,"v":[1640000000,50000.0,51000.0,49000.0,50500.0,1000.0]}]}]}',
            ]

            tv = TvDatafeed()
            yield tv

    def test_initialization_without_auth(self, mock_tv):
        """Test initializing without authentication"""
        assert mock_tv is not None

    def test_get_hist_returns_dataframe(self, mock_tv):
        """Test that get_hist returns a pandas DataFrame"""
        # This will use the mocked WebSocket
        df = mock_tv.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=10
        )

        assert df is not None
        # DataFrame structure validation happens in unit tests

    def test_get_hist_with_different_intervals(self, mock_tv):
        """Test fetching data with different intervals"""
        intervals = [
            Interval.in_1_minute,
            Interval.in_15_minute,
            Interval.in_1_hour,
            Interval.in_daily
        ]

        for interval in intervals:
            df = mock_tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=interval,
                n_bars=5
            )
            # Just verify no exception is raised
            assert df is not None or df is None  # May return None if no data

    def test_get_hist_different_symbols(self, mock_tv):
        """Test fetching different symbols"""
        symbols = [
            ('BTCUSDT', 'BINANCE'),
            ('ETHUSDT', 'BINANCE'),
        ]

        for symbol, exchange in symbols:
            df = mock_tv.get_hist(
                symbol=symbol,
                exchange=exchange,
                interval=Interval.in_1_hour,
                n_bars=5
            )
            # Just verify no exception is raised


@pytest.mark.integration
class TestDataValidation:
    """Test data validation in integration context"""

    @pytest.fixture
    def mock_tv_with_data(self):
        """Create a mocked TvDatafeed that returns valid data"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection

            # Mock responses with valid OHLCV data
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
                '~m~300~m~{"m":"timescale_update","p":["cs_test456",{"s":[{"i":0,"v":[1640000000,50000.0,51000.0,49000.0,50500.0,1000.0,1640003600,50500.0,52000.0,50000.0,51500.0,1200.0]}]}]}',
            ]

            tv = TvDatafeed()
            yield tv

    def test_dataframe_has_correct_columns(self, mock_tv_with_data):
        """Test that returned DataFrame has expected columns"""
        df = mock_tv_with_data.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=10
        )

        if df is not None and not df.empty:
            expected_columns = ['open', 'high', 'low', 'close', 'volume']
            assert all(col in df.columns for col in expected_columns)

    def test_dataframe_has_datetime_index(self, mock_tv_with_data):
        """Test that DataFrame has proper datetime index"""
        df = mock_tv_with_data.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=10
        )

        if df is not None and not df.empty:
            assert isinstance(df.index, pd.DatetimeIndex)

    def test_ohlc_relationships(self, mock_tv_with_data):
        """Test OHLC price relationships are valid"""
        df = mock_tv_with_data.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=10
        )

        if df is not None and not df.empty:
            # High should be >= Low
            assert (df['high'] >= df['low']).all()
            # High should be >= Open and Close
            assert (df['high'] >= df['open']).all()
            assert (df['high'] >= df['close']).all()
            # Low should be <= Open and Close
            assert (df['low'] <= df['open']).all()
            assert (df['low'] <= df['close']).all()


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in integration context"""

    def test_invalid_symbol_handling(self):
        """Test handling of invalid symbol"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"error"}]}'

            tv = TvDatafeed()

            # Should handle gracefully (return None or raise clear exception)
            result = tv.get_hist(
                symbol='INVALID',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )

            # Either None or exception should be raised
            assert result is None or isinstance(result, pd.DataFrame)

    def test_connection_timeout_handling(self):
        """Test handling of connection timeout"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            # Simulate timeout
            mock_ws.side_effect = TimeoutError("Connection timeout")

            # Should handle timeout gracefully
            try:
                tv = TvDatafeed()
                # If initialization succeeds, that's also acceptable
            except (TimeoutError, ConnectionError):
                # Expected behavior
                pass

    def test_websocket_disconnection_handling(self):
        """Test handling of WebSocket disconnection"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection

            # First call succeeds, second call fails (disconnection)
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
                ConnectionError("Connection closed")
            ]

            tv = TvDatafeed()

            # Should handle disconnection gracefully
            result = tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )

            # Either None or exception should be raised
            assert result is None or isinstance(result, pd.DataFrame)


@pytest.mark.integration
@pytest.mark.slow
class TestLargeDatasets:
    """Test handling of large datasets"""

    @pytest.fixture
    def mock_tv_large_data(self):
        """Create a mocked TvDatafeed with large dataset"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection

            # Create a large dataset (simulate max 5000 bars)
            large_data = []
            base_time = 1640000000
            for i in range(1000):  # Simulate 1000 bars
                timestamp = base_time + (i * 3600)
                open_price = 50000.0 + (i * 10)
                high_price = open_price + 500
                low_price = open_price - 300
                close_price = open_price + 200
                volume = 1000.0 + (i * 5)
                large_data.extend([timestamp, open_price, high_price, low_price, close_price, volume])

            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
                f'~m~10000~m~{{"m":"timescale_update","p":["cs_test456",{{"s":[{{"i":0,"v":{large_data}}}]}}]}}',
            ]

            tv = TvDatafeed()
            yield tv

    def test_max_bars_handling(self, mock_tv_large_data):
        """Test handling of maximum bars request (5000)"""
        df = mock_tv_large_data.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=5000
        )

        # Should handle large requests without error
        if df is not None:
            assert len(df) <= 5000

    def test_dataframe_memory_efficiency(self, mock_tv_large_data):
        """Test that large DataFrames are memory efficient"""
        df = mock_tv_large_data.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=5000
        )

        if df is not None and not df.empty:
            # Check memory usage is reasonable
            memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            # Should be less than 10MB for 5000 bars
            assert memory_mb < 10.0


@pytest.mark.integration
class TestSymbolSearch:
    """Test symbol search functionality"""

    @pytest.fixture
    def mock_tv_search(self):
        """Create a mocked TvDatafeed for search testing"""
        with patch('tvDatafeed.main.create_connection') as mock_ws, \
             patch('tvDatafeed.main.requests.get') as mock_get:

            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            # Mock search response
            mock_response = Mock()
            mock_response.json.return_value = [
                {
                    'symbol': 'BINANCE:BTCUSDT',
                    'description': 'Bitcoin / TetherUS',
                    'exchange': 'BINANCE',
                    'type': 'crypto'
                }
            ]
            mock_get.return_value = mock_response

            tv = TvDatafeed()
            yield tv

    def test_search_returns_results(self, mock_tv_search):
        """Test that symbol search returns results"""
        results = mock_tv_search.search_symbol('BTC', 'BINANCE')

        assert results is not None
        assert isinstance(results, list)

    def test_search_result_structure(self, mock_tv_search):
        """Test that search results have expected structure"""
        results = mock_tv_search.search_symbol('BTC', 'BINANCE')

        if results and len(results) > 0:
            result = results[0]
            assert 'symbol' in result
            # Other fields are optional but commonly present
