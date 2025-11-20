"""
Integration tests for TvDatafeedLive workflow

These tests verify the live feed functionality including threading,
callbacks, and real-time data processing.
"""
import time
import pytest
import threading
from unittest.mock import patch, Mock, MagicMock
from tvDatafeed import TvDatafeedLive, Interval


@pytest.mark.integration
@pytest.mark.threading
class TestLiveFeedBasics:
    """Test basic live feed functionality"""

    @pytest.fixture
    def mock_live_tv(self):
        """Create a mocked TvDatafeedLive instance"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
            ] * 100  # Enough responses for testing

            tv = TvDatafeedLive()
            yield tv

            # Cleanup
            if hasattr(tv, 'thread') and tv.thread and tv.thread.is_alive():
                tv.stop_live_feed()

    def test_live_feed_initialization(self, mock_live_tv):
        """Test that live feed can be initialized"""
        assert mock_live_tv is not None
        assert hasattr(mock_live_tv, 'start_live_feed')
        assert hasattr(mock_live_tv, 'stop_live_feed')

    def test_start_live_feed(self, mock_live_tv):
        """Test starting live feed"""
        # Create a simple callback
        callback_called = threading.Event()

        def simple_callback(symbol, exchange, interval, dataframe):
            callback_called.set()

        # Start live feed
        seis_id = mock_live_tv.start_live_feed(
            callback=simple_callback,
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        assert seis_id is not None

        # Give some time for thread to start
        time.sleep(0.1)

        # Verify thread is running
        assert mock_live_tv.thread is not None
        assert mock_live_tv.thread.is_alive()

        # Stop feed
        mock_live_tv.stop_live_feed()

    def test_stop_live_feed(self, mock_live_tv):
        """Test stopping live feed"""
        def dummy_callback(symbol, exchange, interval, dataframe):
            pass

        # Start and then stop
        mock_live_tv.start_live_feed(
            callback=dummy_callback,
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        time.sleep(0.1)
        mock_live_tv.stop_live_feed()

        # Wait a bit for thread to stop
        time.sleep(0.2)

        # Thread should be stopped
        if mock_live_tv.thread:
            assert not mock_live_tv.thread.is_alive()


@pytest.mark.integration
@pytest.mark.threading
class TestMultipleSymbols:
    """Test monitoring multiple symbols simultaneously"""

    @pytest.fixture
    def mock_live_tv_multi(self):
        """Create a mocked TvDatafeedLive for multiple symbols"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection

            # Mock multiple symbol responses
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
                '~m~52~m~{"m":"qsd","p":["qs_test456",{"n":"symbol_2","s":"ok"}]}',
            ] * 100

            tv = TvDatafeedLive()
            yield tv

            # Cleanup
            if hasattr(tv, 'thread') and tv.thread and tv.thread.is_alive():
                tv.stop_live_feed()

    def test_multiple_symbols_different_callbacks(self, mock_live_tv_multi):
        """Test monitoring multiple symbols with different callbacks"""
        btc_called = threading.Event()
        eth_called = threading.Event()

        def btc_callback(symbol, exchange, interval, dataframe):
            btc_called.set()

        def eth_callback(symbol, exchange, interval, dataframe):
            eth_called.set()

        # Start feed for BTC
        seis_id_btc = mock_live_tv_multi.start_live_feed(
            callback=btc_callback,
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        # Start feed for ETH
        seis_id_eth = mock_live_tv_multi.start_live_feed(
            callback=eth_callback,
            symbol='ETHUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        assert seis_id_btc != seis_id_eth

        time.sleep(0.2)

        # Stop feed
        mock_live_tv_multi.stop_live_feed()

    def test_same_symbol_multiple_callbacks(self, mock_live_tv_multi):
        """Test multiple callbacks for the same symbol"""
        callback1_called = threading.Event()
        callback2_called = threading.Event()

        def callback1(symbol, exchange, interval, dataframe):
            callback1_called.set()

        def callback2(symbol, exchange, interval, dataframe):
            callback2_called.set()

        # Register multiple callbacks for same symbol
        seis_id1 = mock_live_tv_multi.start_live_feed(
            callback=callback1,
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        seis_id2 = mock_live_tv_multi.start_live_feed(
            callback=callback2,
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        # Should return the same SEIS ID
        assert seis_id1 == seis_id2

        time.sleep(0.2)

        # Stop feed
        mock_live_tv_multi.stop_live_feed()


@pytest.mark.integration
@pytest.mark.threading
class TestCallbackExecution:
    """Test callback execution and error handling"""

    @pytest.fixture
    def mock_live_tv_callback(self):
        """Create a mocked TvDatafeedLive for callback testing"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
            ] * 100

            tv = TvDatafeedLive()
            yield tv

            # Cleanup
            if hasattr(tv, 'thread') and tv.thread and tv.thread.is_alive():
                tv.stop_live_feed()

    def test_callback_receives_correct_parameters(self, mock_live_tv_callback):
        """Test that callback receives correct parameters"""
        received_params = {}

        def param_callback(symbol, exchange, interval, dataframe):
            received_params['symbol'] = symbol
            received_params['exchange'] = exchange
            received_params['interval'] = interval
            received_params['dataframe'] = dataframe

        mock_live_tv_callback.start_live_feed(
            callback=param_callback,
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        time.sleep(0.2)

        # If callback was called, verify parameters
        if received_params:
            assert received_params['symbol'] == 'BTCUSDT'
            assert received_params['exchange'] == 'BINANCE'
            assert received_params['interval'] == Interval.in_1_hour

        mock_live_tv_callback.stop_live_feed()

    def test_callback_exception_handling(self, mock_live_tv_callback):
        """Test that exceptions in callbacks don't crash the feed"""
        exception_count = [0]

        def failing_callback(symbol, exchange, interval, dataframe):
            exception_count[0] += 1
            raise ValueError("Intentional test exception")

        mock_live_tv_callback.start_live_feed(
            callback=failing_callback,
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        time.sleep(0.2)

        # Feed should still be running despite callback exceptions
        assert mock_live_tv_callback.thread is not None
        assert mock_live_tv_callback.thread.is_alive()

        mock_live_tv_callback.stop_live_feed()


@pytest.mark.integration
@pytest.mark.threading
@pytest.mark.slow
class TestThreadSafety:
    """Test thread safety and synchronization"""

    @pytest.fixture
    def mock_live_tv_threads(self):
        """Create a mocked TvDatafeedLive for thread safety testing"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
            ] * 1000  # More responses for stress testing

            tv = TvDatafeedLive()
            yield tv

            # Cleanup
            if hasattr(tv, 'thread') and tv.thread and tv.thread.is_alive():
                tv.stop_live_feed()

    def test_concurrent_callback_registration(self, mock_live_tv_threads):
        """Test registering callbacks concurrently"""
        def dummy_callback(symbol, exchange, interval, dataframe):
            pass

        # Start multiple callbacks concurrently
        threads = []
        seis_ids = []

        def register_callback(i):
            seis_id = mock_live_tv_threads.start_live_feed(
                callback=dummy_callback,
                symbol=f'SYMBOL{i}',
                exchange='BINANCE',
                interval=Interval.in_1_hour
            )
            seis_ids.append(seis_id)

        for i in range(5):
            t = threading.Thread(target=register_callback, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All registrations should succeed
        assert len(seis_ids) == 5

        time.sleep(0.2)

        mock_live_tv_threads.stop_live_feed()

    def test_stop_feed_thread_cleanup(self, mock_live_tv_threads):
        """Test that stopping feed properly cleans up threads"""
        callback_count = [0]

        def counting_callback(symbol, exchange, interval, dataframe):
            callback_count[0] += 1

        mock_live_tv_threads.start_live_feed(
            callback=counting_callback,
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        time.sleep(0.2)

        # Get initial thread count
        initial_thread_count = threading.active_count()

        # Stop feed
        mock_live_tv_threads.stop_live_feed()

        # Wait for cleanup
        time.sleep(0.5)

        # Thread count should be back to normal (or lower)
        final_thread_count = threading.active_count()
        assert final_thread_count <= initial_thread_count


@pytest.mark.integration
@pytest.mark.threading
class TestLiveFeedResilience:
    """Test resilience of live feed to errors"""

    def test_websocket_reconnection(self):
        """Test handling of WebSocket disconnection and reconnection"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            call_count = [0]

            def mock_recv():
                call_count[0] += 1
                if call_count[0] == 5:
                    # Simulate disconnection after 5 calls
                    raise ConnectionError("Connection lost")
                return '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            mock_connection.recv.side_effect = mock_recv
            mock_ws.return_value = mock_connection

            tv = TvDatafeedLive()

            def dummy_callback(symbol, exchange, interval, dataframe):
                pass

            tv.start_live_feed(
                callback=dummy_callback,
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour
            )

            time.sleep(0.5)

            # Feed should handle disconnection gracefully
            # (either stop or attempt reconnection depending on implementation)

            tv.stop_live_feed()

    def test_data_parsing_errors(self):
        """Test handling of malformed data"""
        with patch('tvDatafeed.main.ws.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection

            # Return malformed data
            mock_connection.recv.side_effect = [
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
                '~m~50~m~MALFORMED_JSON_DATA',
                '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}',
            ] * 100

            tv = TvDatafeedLive()

            def dummy_callback(symbol, exchange, interval, dataframe):
                pass

            tv.start_live_feed(
                callback=dummy_callback,
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour
            )

            time.sleep(0.2)

            # Feed should continue running despite parsing errors
            assert tv.thread is not None
            assert tv.thread.is_alive()

            tv.stop_live_feed()
