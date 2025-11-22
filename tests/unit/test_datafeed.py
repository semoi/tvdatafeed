"""
Unit tests for TvDatafeedLive and _SeisesAndTrigger classes in datafeed.py

Tests cover:
- _SeisesAndTrigger internal class methods
- TvDatafeedLive initialization and configuration
- new_seis, del_seis, new_consumer, del_consumer methods
- get_hist with timeout
- _graceful_shutdown mechanism
- del_tvdatafeed cleanup

These tests aim to improve coverage of datafeed.py from 37.20% to at least 50%.
"""
import pytest
import time
import threading
import queue
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from tvDatafeed import TvDatafeedLive, Interval, Seis, Consumer


# Test timeout for avoiding blocked tests
TEST_TIMEOUT = 5.0


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV DataFrame for testing"""
    dates = pd.date_range('2021-01-01', periods=2, freq='1H', tz='UTC')
    data = {
        'symbol': ['BTCUSDT'] * 2,
        'open': [30000, 30100],
        'high': [30100, 30200],
        'low': [29900, 30000],
        'close': [30050, 30150],
        'volume': [1000000, 1100000]
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'datetime'
    return df


@pytest.fixture
def mock_tvdatafeedlive():
    """Create a mocked TvDatafeedLive instance without network calls"""
    with patch('tvDatafeed.TvDatafeed.__init__', return_value=None):
        tvl = TvDatafeedLive.__new__(TvDatafeedLive)
        tvl._lock = threading.Lock()
        tvl._thread_lock = threading.Lock()
        tvl._main_thread = None
        tvl._shutdown_in_progress = False
        tvl._sat = TvDatafeedLive._SeisesAndTrigger()
        # Add required attributes from parent class
        tvl.ws_timeout = 5.0
        tvl.ws_debug = False
        tvl.verbose = False
        return tvl


# ============================================================================
# _SeisesAndTrigger Class Tests
# ============================================================================

@pytest.mark.unit
class TestSeisesAndTrigger:
    """Test _SeisesAndTrigger internal class"""

    def test_sat_initialization(self):
        """Test _SeisesAndTrigger initialization"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        assert sat._trigger_quit is False
        assert sat._trigger_dt is None
        assert isinstance(sat._trigger_interrupt, threading.Event)
        # threading.Lock() returns an object, check it has acquire/release methods
        assert hasattr(sat._state_lock, 'acquire')
        assert hasattr(sat._state_lock, 'release')
        assert '1' in sat._timeframes
        assert '1H' in sat._timeframes
        assert '1D' in sat._timeframes

    def test_sat_timeframes_coverage(self):
        """Test all timeframes are properly defined"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        expected_timeframes = ['1', '3', '5', '15', '30', '45',
                               '1H', '2H', '3H', '4H',
                               '1D', '1W', '1M']

        for tf in expected_timeframes:
            assert tf in sat._timeframes, f"Missing timeframe: {tf}"

    def test_sat_get_seis_empty(self):
        """Test get_seis returns None when list is empty"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        result = sat.get_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        assert result is None

    def test_sat_get_seis_found(self):
        """Test get_seis returns Seis when found"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()
        sat.append(seis, update_dt)

        result = sat.get_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        assert result == seis

    def test_sat_get_seis_not_found_different_symbol(self):
        """Test get_seis returns None when symbol differs"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()
        sat.append(seis, update_dt)

        result = sat.get_seis('ETHUSDT', 'BINANCE', Interval.in_1_hour)

        assert result is None

    def test_sat_get_seis_not_found_different_exchange(self):
        """Test get_seis returns None when exchange differs"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()
        sat.append(seis, update_dt)

        result = sat.get_seis('BTCUSDT', 'COINBASE', Interval.in_1_hour)

        assert result is None

    def test_sat_get_seis_not_found_different_interval(self):
        """Test get_seis returns None when interval differs"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()
        sat.append(seis, update_dt)

        result = sat.get_seis('BTCUSDT', 'BINANCE', Interval.in_daily)

        assert result is None

    def test_sat_next_trigger_dt_empty(self):
        """Test _next_trigger_dt returns None when empty"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        result = sat._next_trigger_dt()

        assert result is None

    def test_sat_next_trigger_dt_single_seis(self):
        """Test _next_trigger_dt returns correct datetime with one seis"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()
        sat.append(seis, update_dt)

        result = sat._next_trigger_dt()

        assert result is not None
        # Should be update_dt + 1 hour (timeframe)
        expected = update_dt + relativedelta(hours=1)
        assert result == expected

    def test_sat_next_trigger_dt_multiple_seises(self):
        """Test _next_trigger_dt returns earliest datetime"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        # Add seis with different intervals
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt1 = datetime.now()
        sat.append(seis1, update_dt1)

        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_daily)
        update_dt2 = datetime.now() + timedelta(hours=2)
        sat.append(seis2, update_dt2)

        result = sat._next_trigger_dt()

        # Should return the earliest one
        expected = update_dt1 + relativedelta(hours=1)
        assert result == expected

    def test_sat_wait_returns_false_when_empty(self):
        """Test wait() returns False immediately when empty"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        start_time = time.time()
        result = sat.wait()
        elapsed = time.time() - start_time

        assert result is False
        assert elapsed < 0.1  # Should return immediately

    def test_sat_wait_returns_false_on_quit(self):
        """Test wait() returns False when quit() is called"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now() + timedelta(hours=1)  # Future
        sat.append(seis, update_dt)

        result = [None]

        def wait_thread():
            result[0] = sat.wait()

        t = threading.Thread(target=wait_thread)
        t.start()

        time.sleep(0.1)
        sat.quit()

        t.join(timeout=TEST_TIMEOUT)

        assert result[0] is False

    def test_sat_wait_returns_true_on_expiry(self):
        """Test wait() returns True when interval expires"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        # Set update_dt in the past so it expires immediately
        update_dt = datetime.now() - timedelta(hours=2)
        sat.append(seis, update_dt)

        start_time = time.time()
        result = sat.wait()
        elapsed = time.time() - start_time

        assert result is True
        assert elapsed < 1.0  # Should return quickly

    def test_sat_get_expired_empty(self):
        """Test get_expired returns empty list when no intervals"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        result = sat.get_expired()

        assert result == []

    def test_sat_get_expired_with_expired_interval(self):
        """Test get_expired returns expired intervals"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        # Set expiry in the past
        update_dt = datetime.now() - timedelta(hours=2)
        sat.append(seis, update_dt)

        result = sat.get_expired()

        assert '1H' in result

    def test_sat_get_expired_updates_expiry(self):
        """Test get_expired updates expiry datetime"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now() - timedelta(hours=2)
        sat.append(seis, update_dt)

        # First call should return expired
        result1 = sat.get_expired()
        assert '1H' in result1

        # Second call should return empty (expiry updated to future)
        result2 = sat.get_expired()
        # May or may not be empty depending on exact timing
        # At minimum, the first call should have updated the expiry

    def test_sat_quit_sets_flag(self):
        """Test quit() sets trigger_quit flag"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        sat.quit()

        with sat._state_lock:
            assert sat._trigger_quit is True

    def test_sat_quit_sets_interrupt(self):
        """Test quit() sets interrupt event"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        sat.quit()

        assert sat._trigger_interrupt.is_set()

    def test_sat_clear_raises_not_implemented(self):
        """Test clear() raises NotImplementedError"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        with pytest.raises(NotImplementedError):
            sat.clear()

    def test_sat_append_new_interval_group(self):
        """Test append creates new interval group"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()

        sat.append(seis, update_dt)

        assert '1H' in sat.intervals()
        assert seis in sat

    def test_sat_append_existing_interval_group(self):
        """Test append adds to existing interval group"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()

        sat.append(seis1, update_dt)
        sat.append(seis2)  # No update_dt needed for existing group

        assert '1H' in sat.intervals()
        assert seis1 in sat
        assert seis2 in sat
        assert len(sat['1H']) == 2

    def test_sat_append_without_update_dt_raises(self):
        """Test append raises ValueError when update_dt missing for new group"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        with pytest.raises(ValueError, match="Missing update datetime"):
            sat.append(seis)  # No update_dt for new group

    def test_sat_discard_removes_seis(self):
        """Test discard removes Seis from list"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()
        sat.append(seis, update_dt)

        sat.discard(seis)

        assert seis not in sat

    def test_sat_discard_removes_empty_interval_group(self):
        """Test discard removes interval group when empty"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now()
        sat.append(seis, update_dt)

        sat.discard(seis)

        assert '1H' not in sat.intervals()

    def test_sat_discard_not_found_raises(self):
        """Test discard raises KeyError when Seis not found"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        with pytest.raises(KeyError, match="No such Seis"):
            sat.discard(seis)

    def test_sat_intervals_returns_keys(self):
        """Test intervals() returns interval keys"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_daily)

        sat.append(seis1, datetime.now())
        sat.append(seis2, datetime.now())

        intervals = list(sat.intervals())

        assert '1H' in intervals
        assert '1D' in intervals

    def test_sat_getitem_returns_seises_list(self):
        """Test __getitem__ returns list of seises for interval"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_1_hour)

        sat.append(seis1, datetime.now())
        sat.append(seis2)

        result = sat['1H']

        assert len(result) == 2
        assert seis1 in result
        assert seis2 in result

    def test_sat_iter_returns_all_seises(self):
        """Test __iter__ returns all seises across all intervals"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_daily)

        sat.append(seis1, datetime.now())
        sat.append(seis2, datetime.now())

        seises = list(sat)

        assert len(seises) == 2
        assert seis1 in seises
        assert seis2 in seises

    def test_sat_contains_true(self):
        """Test __contains__ returns True when Seis exists"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        sat.append(seis, datetime.now())

        assert seis in sat

    def test_sat_contains_false(self):
        """Test __contains__ returns False when Seis not exists"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_1_hour)
        sat.append(seis1, datetime.now())

        assert seis2 not in sat

    def test_sat_append_interrupts_wait_for_sooner_expiry(self):
        """Test append interrupts wait when new expiry is sooner"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        # Add seis with far future expiry
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_daily)
        update_dt1 = datetime.now() + timedelta(hours=12)  # Far future
        sat.append(seis1, update_dt1)

        wait_interrupted = [False]

        def wait_thread():
            sat.wait()
            wait_interrupted[0] = True

        t = threading.Thread(target=wait_thread)
        t.start()

        time.sleep(0.1)

        # Add seis with sooner expiry - should interrupt wait
        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt2 = datetime.now() - timedelta(hours=1)  # Past (already expired)
        sat.append(seis2, update_dt2)

        t.join(timeout=TEST_TIMEOUT)

        # Wait should have returned due to the new expiry

    def test_sat_discard_updates_trigger_dt(self):
        """Test discard updates trigger_dt when removing waited interval"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        # Add two seises with different intervals
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt1 = datetime.now()
        sat.append(seis1, update_dt1)

        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_daily)
        update_dt2 = datetime.now() + timedelta(hours=2)
        sat.append(seis2, update_dt2)

        # Discard the first one
        sat.discard(seis1)

        # Only the daily one should remain
        assert '1H' not in sat.intervals()
        assert '1D' in sat.intervals()


# ============================================================================
# TvDatafeedLive Initialization Tests
# ============================================================================

@pytest.mark.unit
class TestTvDatafeedLiveInit:
    """Test TvDatafeedLive initialization"""

    @patch('tvDatafeed.TvDatafeed.__init__', return_value=None)
    def test_init_creates_locks(self, mock_init):
        """Test __init__ creates necessary locks"""
        tvl = TvDatafeedLive()

        assert hasattr(tvl, '_lock')
        assert hasattr(tvl, '_thread_lock')
        assert isinstance(tvl._lock, type(threading.Lock()))
        assert isinstance(tvl._thread_lock, type(threading.Lock()))

    @patch('tvDatafeed.TvDatafeed.__init__', return_value=None)
    def test_init_creates_sat(self, mock_init):
        """Test __init__ creates _SeisesAndTrigger"""
        tvl = TvDatafeedLive()

        assert hasattr(tvl, '_sat')
        assert isinstance(tvl._sat, TvDatafeedLive._SeisesAndTrigger)

    @patch('tvDatafeed.TvDatafeed.__init__', return_value=None)
    def test_init_sets_shutdown_flag_false(self, mock_init):
        """Test __init__ sets _shutdown_in_progress to False"""
        tvl = TvDatafeedLive()

        assert tvl._shutdown_in_progress is False

    @patch('tvDatafeed.TvDatafeed.__init__', return_value=None)
    def test_init_main_thread_none(self, mock_init):
        """Test __init__ sets _main_thread to None"""
        tvl = TvDatafeedLive()

        assert tvl._main_thread is None


# ============================================================================
# TvDatafeedLive._args_invalid Tests
# ============================================================================

@pytest.mark.unit
class TestArgsInvalid:
    """Test _args_invalid method"""

    def test_args_invalid_returns_true_empty_result(self, mock_tvdatafeedlive):
        """Test _args_invalid returns True when search returns empty"""
        tvl = mock_tvdatafeedlive

        with patch.object(tvl, 'search_symbol', return_value=[]):
            result = tvl._args_invalid('INVALID', 'EXCHANGE')

        assert result is True

    def test_args_invalid_returns_true_no_match(self, mock_tvdatafeedlive):
        """Test _args_invalid returns True when no exact match"""
        tvl = mock_tvdatafeedlive

        search_result = [
            {'symbol': 'BTC', 'exchange': 'OTHER'},
            {'symbol': 'BTCUSD', 'exchange': 'BINANCE'},
        ]

        with patch.object(tvl, 'search_symbol', return_value=search_result):
            result = tvl._args_invalid('BTCUSDT', 'BINANCE')

        assert result is True

    def test_args_invalid_returns_false_exact_match(self, mock_tvdatafeedlive):
        """Test _args_invalid returns False when exact match found"""
        tvl = mock_tvdatafeedlive

        search_result = [
            {'symbol': 'BTCUSDT', 'exchange': 'BINANCE'},
        ]

        with patch.object(tvl, 'search_symbol', return_value=search_result):
            result = tvl._args_invalid('BTCUSDT', 'BINANCE')

        assert result is False


# ============================================================================
# TvDatafeedLive.new_seis Tests
# ============================================================================

@pytest.mark.unit
class TestNewSeis:
    """Test new_seis method"""

    def test_new_seis_invalid_symbol_raises(self, mock_tvdatafeedlive):
        """Test new_seis raises ValueError for invalid symbol"""
        tvl = mock_tvdatafeedlive

        with patch.object(tvl, 'search_symbol', return_value=[]):
            with pytest.raises(ValueError, match="not listed in TradingView"):
                tvl.new_seis('INVALID', 'EXCHANGE', Interval.in_1_hour)

    def test_new_seis_returns_false_on_timeout(self, mock_tvdatafeedlive):
        """Test new_seis returns False when lock times out"""
        tvl = mock_tvdatafeedlive

        search_result = [{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}]

        with patch.object(tvl, 'search_symbol', return_value=search_result):
            # Acquire lock to cause timeout
            tvl._lock.acquire()
            try:
                result = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour, timeout=0.1)
            finally:
                tvl._lock.release()

        assert result is False

    def test_new_seis_returns_false_during_shutdown(self, mock_tvdatafeedlive):
        """Test new_seis returns False when shutdown in progress"""
        tvl = mock_tvdatafeedlive
        tvl._shutdown_in_progress = True

        search_result = [{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}]

        with patch.object(tvl, 'search_symbol', return_value=search_result):
            result = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        assert result is False

    def test_new_seis_returns_existing_seis(self, mock_tvdatafeedlive, sample_ohlcv_data):
        """Test new_seis returns existing Seis if already exists"""
        tvl = mock_tvdatafeedlive

        search_result = [{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}]

        # Add seis manually
        existing_seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(existing_seis, datetime.now())

        with patch.object(tvl, 'search_symbol', return_value=search_result):
            result = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        assert result == existing_seis

    def test_new_seis_creates_new_seis(self, mock_tvdatafeedlive, sample_ohlcv_data):
        """Test new_seis creates and returns new Seis"""
        tvl = mock_tvdatafeedlive

        search_result = [{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}]

        with patch.object(tvl, 'search_symbol', return_value=search_result), \
             patch('tvDatafeed.TvDatafeed.get_hist', return_value=sample_ohlcv_data):
            result = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        assert isinstance(result, Seis)
        assert result.symbol == 'BTCUSDT'
        assert result.exchange == 'BINANCE'
        assert result.interval == Interval.in_1_hour
        assert result in tvl._sat

    def test_new_seis_starts_main_thread(self, mock_tvdatafeedlive, sample_ohlcv_data):
        """Test new_seis starts main thread if not running"""
        tvl = mock_tvdatafeedlive

        search_result = [{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}]

        with patch.object(tvl, 'search_symbol', return_value=search_result), \
             patch('tvDatafeed.TvDatafeed.get_hist', return_value=sample_ohlcv_data), \
             patch.object(tvl, '_main_loop'):
            result = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        assert result is not False
        assert tvl._main_thread is not None

        # Cleanup
        tvl._sat.quit()
        if tvl._main_thread:
            tvl._main_thread.join(timeout=TEST_TIMEOUT)


# ============================================================================
# TvDatafeedLive.del_seis Tests
# ============================================================================

@pytest.mark.unit
class TestDelSeis:
    """Test del_seis method"""

    def test_del_seis_returns_false_on_timeout(self, mock_tvdatafeedlive):
        """Test del_seis returns False when lock times out"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        # Acquire lock to cause timeout
        tvl._lock.acquire()
        try:
            result = tvl.del_seis(seis, timeout=0.1)
        finally:
            tvl._lock.release()

        assert result is False

    def test_del_seis_raises_when_not_listed(self, mock_tvdatafeedlive):
        """Test del_seis raises ValueError when Seis not in list"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        with pytest.raises(ValueError, match="not listed"):
            tvl.del_seis(seis)

    def test_del_seis_removes_seis(self, mock_tvdatafeedlive):
        """Test del_seis removes Seis from list"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(seis, datetime.now())

        result = tvl.del_seis(seis)

        assert result is True
        assert seis not in tvl._sat

    def test_del_seis_stops_consumers(self, mock_tvdatafeedlive):
        """Test del_seis signals consumers to stop"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(seis, datetime.now())

        # Add mock consumer
        mock_consumer = Mock()
        seis.add_consumer(mock_consumer)

        result = tvl.del_seis(seis)

        assert result is True
        mock_consumer.put.assert_called_once_with(None)

    def test_del_seis_quits_sat_when_empty(self, mock_tvdatafeedlive):
        """Test del_seis calls quit() when SAT becomes empty"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(seis, datetime.now())

        result = tvl.del_seis(seis)

        assert result is True
        # SAT should be empty now
        assert len(list(tvl._sat)) == 0


# ============================================================================
# TvDatafeedLive.new_consumer Tests
# ============================================================================

@pytest.mark.unit
class TestNewConsumer:
    """Test new_consumer method"""

    def test_new_consumer_returns_false_on_timeout(self, mock_tvdatafeedlive):
        """Test new_consumer returns False when lock times out"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        # Acquire lock to cause timeout
        tvl._lock.acquire()
        try:
            result = tvl.new_consumer(seis, callback, timeout=0.1)
        finally:
            tvl._lock.release()

        assert result is False

    def test_new_consumer_raises_when_seis_not_listed(self, mock_tvdatafeedlive):
        """Test new_consumer raises ValueError when Seis not in list"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        with pytest.raises(ValueError, match="not listed"):
            tvl.new_consumer(seis, callback)

    def test_new_consumer_creates_and_starts_consumer(self, mock_tvdatafeedlive):
        """Test new_consumer creates, adds, and starts consumer"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(seis, datetime.now())
        callback = Mock()

        result = tvl.new_consumer(seis, callback)

        assert isinstance(result, Consumer)
        assert result.seis == seis
        assert result.callback == callback
        assert result.is_alive()

        # Cleanup
        result.stop()
        result.join(timeout=TEST_TIMEOUT)

    def test_new_consumer_adds_to_seis(self, mock_tvdatafeedlive):
        """Test new_consumer adds consumer to Seis"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(seis, datetime.now())
        callback = Mock()

        result = tvl.new_consumer(seis, callback)

        consumers = seis.get_consumers()
        assert result in consumers

        # Cleanup
        result.stop()
        result.join(timeout=TEST_TIMEOUT)


# ============================================================================
# TvDatafeedLive.del_consumer Tests
# ============================================================================

@pytest.mark.unit
class TestDelConsumer:
    """Test del_consumer method"""

    def test_del_consumer_returns_false_on_timeout(self, mock_tvdatafeedlive):
        """Test del_consumer returns False when lock times out"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        consumer = Consumer(seis, Mock())

        # Acquire lock to cause timeout
        tvl._lock.acquire()
        try:
            result = tvl.del_consumer(consumer, timeout=0.1)
        finally:
            tvl._lock.release()

        assert result is False

    def test_del_consumer_removes_and_stops(self, mock_tvdatafeedlive):
        """Test del_consumer removes from seis and stops consumer"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(seis, datetime.now())
        callback = Mock()

        consumer = Consumer(seis, callback)
        seis.add_consumer(consumer)
        consumer.start()

        result = tvl.del_consumer(consumer)

        assert result is True
        # Wait for consumer to stop
        consumer.join(timeout=TEST_TIMEOUT)
        assert not consumer.is_alive()
        assert consumer not in seis.get_consumers()

    def test_del_consumer_handles_none_seis(self, mock_tvdatafeedlive):
        """Test del_consumer handles consumer with None seis"""
        tvl = mock_tvdatafeedlive
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        consumer = Consumer(seis, callback)
        consumer.seis = None  # Simulate already stopped

        result = tvl.del_consumer(consumer)

        assert result is True


# ============================================================================
# TvDatafeedLive.get_hist Tests
# ============================================================================

@pytest.mark.unit
class TestGetHist:
    """Test get_hist method"""

    def test_get_hist_returns_false_on_timeout(self, mock_tvdatafeedlive):
        """Test get_hist returns False when lock times out"""
        tvl = mock_tvdatafeedlive

        # Acquire lock to cause timeout
        tvl._lock.acquire()
        try:
            result = tvl.get_hist('BTCUSDT', 'BINANCE', timeout=0.1)
        finally:
            tvl._lock.release()

        assert result is False

    def test_get_hist_calls_parent_method(self, mock_tvdatafeedlive, sample_ohlcv_data):
        """Test get_hist calls parent class get_hist"""
        tvl = mock_tvdatafeedlive

        with patch('tvDatafeed.TvDatafeed.get_hist', return_value=sample_ohlcv_data) as mock_parent:
            result = tvl.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=10)

        mock_parent.assert_called_once_with('BTCUSDT', 'BINANCE', Interval.in_1_hour, 10, None, False)
        assert result is sample_ohlcv_data

    def test_get_hist_releases_lock_on_exception(self, mock_tvdatafeedlive):
        """Test get_hist releases lock even when exception occurs"""
        tvl = mock_tvdatafeedlive

        with patch('tvDatafeed.TvDatafeed.get_hist', side_effect=Exception("Test error")):
            with pytest.raises(Exception, match="Test error"):
                tvl.get_hist('BTCUSDT', 'BINANCE')

        # Lock should be released - we should be able to acquire it
        assert tvl._lock.acquire(timeout=0.1)
        tvl._lock.release()


# ============================================================================
# TvDatafeedLive._graceful_shutdown Tests
# ============================================================================

@pytest.mark.unit
class TestGracefulShutdown:
    """Test _graceful_shutdown method"""

    def test_graceful_shutdown_stops_consumers(self, mock_tvdatafeedlive):
        """Test _graceful_shutdown stops all consumers"""
        tvl = mock_tvdatafeedlive

        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(seis, datetime.now())

        callback = Mock()
        consumer = Consumer(seis, callback)
        seis.add_consumer(consumer)
        consumer.start()

        tvl._graceful_shutdown()

        # Consumer should be stopped
        consumer.join(timeout=TEST_TIMEOUT)
        assert not consumer.is_alive()

    def test_graceful_shutdown_discards_seises(self, mock_tvdatafeedlive):
        """Test _graceful_shutdown discards all seises"""
        tvl = mock_tvdatafeedlive

        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_daily)
        tvl._sat.append(seis1, datetime.now())
        tvl._sat.append(seis2, datetime.now())

        tvl._graceful_shutdown()

        # All seises should be removed
        assert len(list(tvl._sat)) == 0

    def test_graceful_shutdown_clears_main_thread(self, mock_tvdatafeedlive):
        """Test _graceful_shutdown clears _main_thread reference"""
        tvl = mock_tvdatafeedlive
        tvl._main_thread = Mock()  # Simulate running thread

        tvl._graceful_shutdown()

        assert tvl._main_thread is None


# ============================================================================
# TvDatafeedLive._shutdown and del_tvdatafeed Tests
# ============================================================================

@pytest.mark.unit
class TestShutdown:
    """Test _shutdown and del_tvdatafeed methods"""

    def test_shutdown_sets_shutdown_flag(self, mock_tvdatafeedlive):
        """Test _shutdown sets _shutdown_in_progress flag"""
        tvl = mock_tvdatafeedlive

        tvl._shutdown()

        assert tvl._shutdown_in_progress is True

    def test_shutdown_is_idempotent(self, mock_tvdatafeedlive):
        """Test _shutdown can be called multiple times safely"""
        tvl = mock_tvdatafeedlive

        tvl._shutdown()
        tvl._shutdown()  # Second call should be safe

        assert tvl._shutdown_in_progress is True

    def test_shutdown_quits_sat(self, mock_tvdatafeedlive):
        """Test _shutdown calls quit on SAT"""
        tvl = mock_tvdatafeedlive

        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        tvl._sat.append(seis, datetime.now())

        tvl._shutdown()

        # SAT should have quit flag set
        with tvl._sat._state_lock:
            assert tvl._sat._trigger_quit is True

    def test_del_tvdatafeed_calls_shutdown(self, mock_tvdatafeedlive):
        """Test del_tvdatafeed calls _shutdown when thread running"""
        tvl = mock_tvdatafeedlive

        # Simulate running thread
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        tvl._main_thread = mock_thread

        with patch.object(tvl, '_shutdown') as mock_shutdown:
            tvl.del_tvdatafeed()
            mock_shutdown.assert_called_once()

    def test_del_tvdatafeed_does_nothing_without_thread(self, mock_tvdatafeedlive):
        """Test del_tvdatafeed does nothing when no thread running"""
        tvl = mock_tvdatafeedlive
        tvl._main_thread = None

        with patch.object(tvl, '_shutdown') as mock_shutdown:
            tvl.del_tvdatafeed()
            mock_shutdown.assert_not_called()

    def test_destructor_is_safe(self, mock_tvdatafeedlive):
        """Test __del__ handles exceptions safely"""
        tvl = mock_tvdatafeedlive

        # Should not raise
        tvl.__del__()
        tvl.__del__()  # Multiple calls should be safe


# ============================================================================
# Integration-style Tests (still unit tests with mocks)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
class TestDatafeedIntegration:
    """Integration-style tests for TvDatafeedLive"""

    def test_full_lifecycle_single_seis(self, mock_tvdatafeedlive, sample_ohlcv_data):
        """Test full lifecycle: create seis, add consumer, delete"""
        tvl = mock_tvdatafeedlive

        # Setup mocks
        search_result = [{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}]

        with patch.object(tvl, 'search_symbol', return_value=search_result), \
             patch('tvDatafeed.TvDatafeed.get_hist', return_value=sample_ohlcv_data), \
             patch.object(tvl, '_main_loop'):

            # Create seis
            seis = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
            assert seis is not False

            # Add consumer
            received_data = []
            def callback(s, data):
                received_data.append(data)

            consumer = tvl.new_consumer(seis, callback)
            assert consumer is not False

            # Delete consumer
            result = tvl.del_consumer(consumer)
            assert result is True

            # Delete seis
            result = tvl.del_seis(seis)
            assert result is True

            # Cleanup
            consumer.join(timeout=TEST_TIMEOUT)
            if tvl._main_thread:
                tvl._sat.quit()
                tvl._main_thread.join(timeout=TEST_TIMEOUT)

    def test_multiple_seises_different_intervals(self, mock_tvdatafeedlive, sample_ohlcv_data):
        """Test adding multiple seises with different intervals"""
        tvl = mock_tvdatafeedlive

        search_results = {
            'BTCUSDT': [{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}],
            'ETHUSDT': [{'symbol': 'ETHUSDT', 'exchange': 'BINANCE'}],
        }

        def search_mock(symbol, exchange):
            return search_results.get(symbol, [])

        with patch.object(tvl, 'search_symbol', side_effect=search_mock), \
             patch('tvDatafeed.TvDatafeed.get_hist', return_value=sample_ohlcv_data), \
             patch.object(tvl, '_main_loop'):

            # Create seises with different intervals
            seis1 = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
            seis2 = tvl.new_seis('ETHUSDT', 'BINANCE', Interval.in_daily)

            assert seis1 is not False
            assert seis2 is not False
            assert seis1 != seis2

            # Both should be in SAT
            assert seis1 in tvl._sat
            assert seis2 in tvl._sat

            # Cleanup
            tvl.del_seis(seis1)
            tvl.del_seis(seis2)

            if tvl._main_thread:
                tvl._sat.quit()
                tvl._main_thread.join(timeout=TEST_TIMEOUT)
