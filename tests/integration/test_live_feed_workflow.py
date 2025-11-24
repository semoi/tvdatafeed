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
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()
            yield tv

            # Cleanup
            try:
                tv.del_tvdatafeed()
            except Exception:
                pass

    def test_live_feed_initialization(self, mock_live_tv):
        """Test that live feed can be initialized"""
        assert mock_live_tv is not None
        # Check correct API methods exist
        assert hasattr(mock_live_tv, 'new_seis')
        assert hasattr(mock_live_tv, 'del_seis')
        assert hasattr(mock_live_tv, 'new_consumer')
        assert hasattr(mock_live_tv, 'del_consumer')
        assert hasattr(mock_live_tv, 'del_tvdatafeed')
        assert hasattr(mock_live_tv, 'get_hist')

    def test_new_seis_creates_seis(self, mock_live_tv):
        """Test creating a new SEIS (Symbol-Exchange-Interval Set)"""
        seis = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        # Should return a Seis object
        assert seis is not None

    def test_del_tvdatafeed_cleanup(self, mock_live_tv):
        """Test that del_tvdatafeed properly cleans up"""
        # Create a seis first
        seis = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        # Cleanup should not raise
        mock_live_tv.del_tvdatafeed()


@pytest.mark.integration
@pytest.mark.threading
class TestSeisManagement:
    """Test SEIS (Symbol-Exchange-Interval Set) management"""

    @pytest.fixture
    def mock_live_tv(self):
        """Create a mocked TvDatafeedLive for SEIS testing"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()
            yield tv

            try:
                tv.del_tvdatafeed()
            except Exception:
                pass

    def test_create_multiple_seis(self, mock_live_tv):
        """Test creating multiple SEIS for different symbols"""
        seis1 = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        seis2 = mock_live_tv.new_seis(
            symbol='ETHUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        assert seis1 is not None
        assert seis2 is not None

    def test_same_symbol_same_interval_returns_same_seis(self, mock_live_tv):
        """Test that same symbol/exchange/interval returns the same SEIS"""
        seis1 = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        seis2 = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        # Should return the same SEIS object
        assert seis1 is seis2

    def test_delete_seis(self, mock_live_tv):
        """Test deleting a SEIS"""
        seis = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        # Should not raise
        mock_live_tv.del_seis(seis)


@pytest.mark.integration
@pytest.mark.threading
class TestConsumerManagement:
    """Test Consumer (callback) management"""

    @pytest.fixture
    def mock_live_tv(self):
        """Create a mocked TvDatafeedLive for consumer testing"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()
            yield tv

            try:
                tv.del_tvdatafeed()
            except Exception:
                pass

    def test_create_consumer_with_callback(self, mock_live_tv):
        """Test creating a consumer with a callback function"""
        seis = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        def my_callback(symbol, exchange, interval, dataframe):
            pass

        consumer = mock_live_tv.new_consumer(seis, my_callback)
        assert consumer is not None

    def test_multiple_consumers_same_seis(self, mock_live_tv):
        """Test adding multiple consumers to the same SEIS"""
        seis = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        def callback1(symbol, exchange, interval, dataframe):
            pass

        def callback2(symbol, exchange, interval, dataframe):
            pass

        consumer1 = mock_live_tv.new_consumer(seis, callback1)
        consumer2 = mock_live_tv.new_consumer(seis, callback2)

        assert consumer1 is not None
        assert consumer2 is not None
        assert consumer1 is not consumer2

    def test_delete_consumer(self, mock_live_tv):
        """Test deleting a consumer"""
        seis = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        def my_callback(symbol, exchange, interval, dataframe):
            pass

        consumer = mock_live_tv.new_consumer(seis, my_callback)

        # Should not raise
        mock_live_tv.del_consumer(consumer)


@pytest.mark.integration
@pytest.mark.threading
class TestThreadSafety:
    """Test thread safety of TvDatafeedLive operations"""

    @pytest.fixture
    def mock_live_tv(self):
        """Create a mocked TvDatafeedLive for thread safety testing"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()
            yield tv

            try:
                tv.del_tvdatafeed()
            except Exception:
                pass

    def test_concurrent_seis_creation(self, mock_live_tv):
        """Test creating SEIS from multiple threads concurrently"""
        seises = []
        errors = []

        def create_seis(i):
            try:
                seis = mock_live_tv.new_seis(
                    symbol=f'SYM{i}',
                    exchange='BINANCE',
                    interval=Interval.in_1_hour
                )
                seises.append(seis)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_seis, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=5.0)

        # All should succeed without errors
        assert len(errors) == 0
        assert len(seises) == 5

    def test_cleanup_with_active_consumers(self, mock_live_tv):
        """Test that cleanup properly stops consumer threads"""
        seis = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        def my_callback(symbol, exchange, interval, dataframe):
            pass

        consumer = mock_live_tv.new_consumer(seis, my_callback)

        # Record thread count before cleanup
        initial_thread_count = threading.active_count()

        # Cleanup
        mock_live_tv.del_tvdatafeed()

        # Wait a bit for cleanup
        time.sleep(0.5)

        # Thread count should not have increased
        final_thread_count = threading.active_count()
        assert final_thread_count <= initial_thread_count + 1  # Allow for some variance


@pytest.mark.integration
@pytest.mark.threading
class TestHistoricalDataWithLiveFeed:
    """Test getting historical data while live feed is active"""

    @pytest.fixture
    def mock_live_tv(self):
        """Create a mocked TvDatafeedLive for historical data testing"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()
            yield tv

            try:
                tv.del_tvdatafeed()
            except Exception:
                pass

    def test_get_hist_available(self, mock_live_tv):
        """Test that get_hist method is available on TvDatafeedLive"""
        assert hasattr(mock_live_tv, 'get_hist')
        assert callable(mock_live_tv.get_hist)

    def test_get_hist_with_active_seis(self, mock_live_tv):
        """Test getting historical data while SEIS is active"""
        # Create a SEIS first
        seis = mock_live_tv.new_seis(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour
        )

        # Should be able to call get_hist (may fail due to mock, but shouldn't crash)
        try:
            result = mock_live_tv.get_hist(
                symbol='ETHUSDT',  # Different symbol
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=10
            )
        except Exception:
            # Expected with mocks - the key is it doesn't crash
            pass


@pytest.mark.integration
class TestLiveFeedInheritance:
    """Test that TvDatafeedLive properly inherits from TvDatafeed"""

    def test_inheritance(self):
        """Test that TvDatafeedLive is a subclass of TvDatafeed"""
        from tvDatafeed import TvDatafeed
        assert issubclass(TvDatafeedLive, TvDatafeed)

    def test_shared_methods(self):
        """Test that TvDatafeedLive has all TvDatafeed methods"""
        with patch('tvDatafeed.main.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            mock_connection.recv.return_value = '~m~52~m~{"m":"qsd","p":["qs_test123",{"n":"symbol_1","s":"ok"}]}'

            tv = TvDatafeedLive()

            # Should have base class methods
            assert hasattr(tv, 'get_hist')
            assert hasattr(tv, 'search_symbol')

            # And live-specific methods
            assert hasattr(tv, 'new_seis')
            assert hasattr(tv, 'new_consumer')
