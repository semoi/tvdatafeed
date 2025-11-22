"""
Unit tests for threading safety and concurrency in tvDatafeed

Tests cover:
- Race conditions protection
- Graceful shutdown mechanisms
- Stress tests under high load
- Deadlock detection with timeouts

These tests validate Phase 3 corrections for:
- seis.py (Seis class thread safety)
- consumer.py (Consumer class thread safety)
- datafeed.py (TvDatafeedLive class thread safety)
"""
import pytest
import time
import threading
import queue
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from tvDatafeed import Seis, Consumer, Interval, TvDatafeedLive


# Test timeout for avoiding blocked tests
TEST_TIMEOUT = 5.0
STRESS_TEST_THREADS = 20
STRESS_TEST_ITERATIONS = 100


@pytest.fixture
def sample_data():
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
def sample_data_generator():
    """Generator for unique sample data with different timestamps"""
    def generate(index=0):
        base_date = pd.Timestamp('2021-01-01', tz='UTC') + pd.Timedelta(hours=index)
        dates = pd.date_range(base_date, periods=2, freq='1H', tz='UTC')
        data = {
            'symbol': ['BTCUSDT'] * 2,
            'open': [30000 + index * 100, 30100 + index * 100],
            'high': [30100 + index * 100, 30200 + index * 100],
            'low': [29900 + index * 100, 30000 + index * 100],
            'close': [30050 + index * 100, 30150 + index * 100],
            'volume': [1000000 + index * 10000, 1100000 + index * 10000]
        }
        df = pd.DataFrame(data, index=dates)
        df.index.name = 'datetime'
        return df
    return generate


# ============================================================================
# Seis Thread Safety Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
class TestSeisThreadSafety:
    """Test Seis class thread safety"""

    def test_concurrent_add_consumer(self):
        """Test concurrent addition of consumers to Seis"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        num_threads = STRESS_TEST_THREADS
        errors = []

        def add_consumer(i):
            try:
                consumer = Mock()
                consumer.name = f"consumer_{i}"
                seis.add_consumer(consumer)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_consumer, args=(i,))
                   for i in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        assert len(errors) == 0, f"Errors during concurrent add: {errors}"
        assert len(seis.get_consumers()) == num_threads

    def test_concurrent_pop_consumer(self):
        """Test concurrent removal of consumers from Seis"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        consumers = [Mock() for _ in range(STRESS_TEST_THREADS)]

        # Add consumers first
        for c in consumers:
            seis.add_consumer(c)

        errors = []

        def pop_consumer(consumer):
            try:
                seis.pop_consumer(consumer)
            except NameError:
                # Expected if consumer already removed
                pass
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=pop_consumer, args=(c,))
                   for c in consumers]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        # Only unexpected errors should be caught
        unexpected_errors = [e for e in errors if not isinstance(e, NameError)]
        assert len(unexpected_errors) == 0, f"Unexpected errors: {unexpected_errors}"
        assert len(seis.get_consumers()) == 0

    def test_concurrent_add_and_pop_consumer(self):
        """Test concurrent addition and removal of consumers"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        errors = []
        operation_count = {'add': 0, 'pop': 0}

        def add_and_pop():
            try:
                consumer = Mock()
                seis.add_consumer(consumer)
                operation_count['add'] += 1
                time.sleep(0.001)  # Small delay
                seis.pop_consumer(consumer)
                operation_count['pop'] += 1
            except NameError:
                # Expected race condition - consumer already removed
                pass
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_and_pop)
                   for _ in range(STRESS_TEST_THREADS)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        assert len(errors) == 0, f"Errors: {errors}"

    def test_concurrent_is_new_data(self, sample_data_generator):
        """Test concurrent access to is_new_data method"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        errors = []
        new_data_count = [0]  # Use list for mutable closure

        def check_new_data(index):
            try:
                data = sample_data_generator(index)
                if seis.is_new_data(data):
                    new_data_count[0] += 1
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=check_new_data, args=(i,))
                   for i in range(STRESS_TEST_THREADS)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        assert len(errors) == 0, f"Errors: {errors}"
        # At least one should be detected as new (the last one processed)
        assert new_data_count[0] >= 1

    def test_get_consumers_returns_copy(self):
        """Test that get_consumers returns a copy, not the original list"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        consumer1 = Mock()
        consumer2 = Mock()

        seis.add_consumer(consumer1)
        consumers_copy = seis.get_consumers()

        # Modify the copy
        consumers_copy.append(consumer2)

        # Original should be unchanged
        assert len(seis.get_consumers()) == 1
        assert consumer2 not in seis.get_consumers()

    def test_concurrent_get_consumers_while_modifying(self):
        """Test concurrent get_consumers while adding/removing"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        errors = []

        def modifier():
            for _ in range(STRESS_TEST_ITERATIONS):
                try:
                    consumer = Mock()
                    seis.add_consumer(consumer)
                    time.sleep(0.0001)
                    seis.pop_consumer(consumer)
                except NameError:
                    pass
                except Exception as e:
                    errors.append(e)

        def reader():
            for _ in range(STRESS_TEST_ITERATIONS):
                try:
                    consumers = seis.get_consumers()
                    # Iterate over the copy
                    for c in consumers:
                        _ = c.name if hasattr(c, 'name') else None
                except Exception as e:
                    errors.append(e)

        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=modifier))
            threads.append(threading.Thread(target=reader))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        assert len(errors) == 0, f"Errors during concurrent read/modify: {errors}"


# ============================================================================
# Consumer Thread Safety Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
class TestConsumerThreadSafety:
    """Test Consumer class thread safety"""

    def test_concurrent_property_access(self, sample_data):
        """Test concurrent access to seis and callback properties"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()
        consumer = Consumer(seis, callback)
        errors = []

        def read_properties():
            try:
                for _ in range(STRESS_TEST_ITERATIONS):
                    _ = consumer.seis
                    _ = consumer.callback
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_properties)
                   for _ in range(STRESS_TEST_THREADS)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        assert len(errors) == 0, f"Errors: {errors}"

    def test_concurrent_stop_calls(self):
        """Test concurrent stop() calls don't cause issues"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()
        consumer = Consumer(seis, callback)
        consumer.start()

        errors = []

        def stop_consumer():
            try:
                consumer.stop()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=stop_consumer)
                   for _ in range(STRESS_TEST_THREADS)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        # Wait for consumer to finish
        consumer.join(timeout=TEST_TIMEOUT)

        assert len(errors) == 0, f"Errors: {errors}"
        assert not consumer.is_alive()

    def test_concurrent_put_operations(self, sample_data):
        """Test concurrent put operations to consumer buffer"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        received_count = [0]
        lock = threading.Lock()

        def callback(s, data):
            with lock:
                received_count[0] += 1

        consumer = Consumer(seis, callback)
        consumer.start()

        errors = []

        def put_data():
            try:
                for _ in range(10):
                    consumer.put(sample_data)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=put_data)
                   for _ in range(STRESS_TEST_THREADS)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        # Give time for processing
        time.sleep(0.5)

        consumer.stop()
        consumer.join(timeout=TEST_TIMEOUT)

        assert len(errors) == 0, f"Errors: {errors}"
        # Most data should have been processed
        assert received_count[0] > 0

    def test_put_after_stop(self, sample_data):
        """Test that put() after stop() doesn't hang or crash"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()
        consumer = Consumer(seis, callback)
        consumer.start()

        consumer.stop()
        consumer.join(timeout=TEST_TIMEOUT)

        # This should not hang or raise
        start_time = time.time()
        consumer.put(sample_data)
        elapsed = time.time() - start_time

        # Should return quickly (not hang)
        assert elapsed < 1.0

    def test_stop_while_processing(self, sample_data):
        """Test stopping consumer while it's processing data"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        processing_event = threading.Event()

        def slow_callback(s, data):
            processing_event.set()
            time.sleep(0.5)  # Simulate slow processing

        consumer = Consumer(seis, slow_callback)
        consumer.start()

        # Put data and wait for processing to start
        consumer.put(sample_data)
        processing_event.wait(timeout=TEST_TIMEOUT)

        # Stop while processing
        consumer.stop()

        # Should terminate within timeout
        consumer.join(timeout=TEST_TIMEOUT)
        assert not consumer.is_alive()

    def test_consumer_cleans_up_on_stop(self):
        """Test that consumer properly cleans up references on stop"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()
        consumer = Consumer(seis, callback)
        consumer.start()

        # Stop and wait
        consumer.stop()
        consumer.join(timeout=TEST_TIMEOUT)

        # References should be cleaned up
        assert consumer.seis is None
        assert consumer.callback is None


# ============================================================================
# TvDatafeedLive Thread Safety Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
class TestTvDatafeedLiveThreadSafety:
    """Test TvDatafeedLive class thread safety"""

    def test_concurrent_lock_access(self, sample_data):
        """Test concurrent access to TvDatafeedLive lock mechanisms

        This test verifies that concurrent lock operations on TvDatafeedLive
        don't cause deadlocks or race conditions.
        """
        # Mock at class level to intercept super().get_hist() calls
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

            errors = []
            access_count = [0]
            count_lock = threading.Lock()

            def access_locks():
                """Simulate concurrent lock access patterns"""
                try:
                    for _ in range(50):
                        # Pattern 1: Acquire _lock with timeout
                        if tvl._lock.acquire(timeout=0.1):
                            with count_lock:
                                access_count[0] += 1
                            time.sleep(0.001)
                            tvl._lock.release()

                        # Pattern 2: Acquire _thread_lock
                        with tvl._thread_lock:
                            _ = tvl._main_thread
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=access_locks)
                       for _ in range(STRESS_TEST_THREADS)]

            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=TEST_TIMEOUT)

            assert len(errors) == 0, f"Errors: {errors}"
            # Should have had many successful accesses
            assert access_count[0] > 0

    def test_lock_timeout_handling(self, sample_data):
        """Test that lock acquisition respects timeout parameter"""
        # Mock at class level to intercept super().get_hist() calls
        with patch('tvDatafeed.TvDatafeed.__init__', return_value=None), \
             patch('tvDatafeed.TvDatafeed.get_hist', return_value=sample_data), \
             patch('tvDatafeed.TvDatafeed.search_symbol', return_value=[{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}]):

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

            # Acquire lock to block other operations
            tvl._lock.acquire()

            # Try to create seis with short timeout
            start_time = time.time()
            result = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour, timeout=0.1)
            elapsed = time.time() - start_time

            tvl._lock.release()

            # Should timeout and return False
            assert result is False
            assert elapsed < 0.5  # Should not take too long

    def test_shutdown_prevents_new_operations(self):
        """Test that shutdown flag prevents new operations"""
        # Mock at class level to intercept search_symbol calls
        with patch('tvDatafeed.TvDatafeed.__init__', return_value=None), \
             patch('tvDatafeed.TvDatafeed.search_symbol', return_value=[{'symbol': 'BTCUSDT', 'exchange': 'BINANCE'}]):

            tvl = TvDatafeedLive.__new__(TvDatafeedLive)
            tvl._lock = threading.Lock()
            tvl._thread_lock = threading.Lock()
            tvl._main_thread = None
            tvl._shutdown_in_progress = True  # Set shutdown flag
            tvl._sat = TvDatafeedLive._SeisesAndTrigger()
            # Add required attributes from parent class
            tvl.ws_timeout = 5.0
            tvl.ws_debug = False
            tvl.verbose = False

            result = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_hour, timeout=0.1)

            assert result is False


# ============================================================================
# Graceful Shutdown Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
class TestGracefulShutdown:
    """Test graceful shutdown mechanisms"""

    def test_consumer_graceful_stop(self, sample_data):
        """Test that consumer stops gracefully with queued data"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        processed = []

        def callback(s, data):
            processed.append(data)
            time.sleep(0.1)

        consumer = Consumer(seis, callback)
        consumer.start()

        # Queue multiple items
        for _ in range(3):
            consumer.put(sample_data)

        # Stop while queue not empty
        consumer.stop()

        # Should still terminate within reasonable time
        consumer.join(timeout=TEST_TIMEOUT)
        assert not consumer.is_alive()

    def test_consumer_stop_with_none_signal(self):
        """Test that None signal properly stops consumer"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()
        consumer = Consumer(seis, callback)
        consumer.start()

        assert consumer.is_alive()

        # Directly put None (internal stop signal)
        consumer._buffer.put(None)

        consumer.join(timeout=TEST_TIMEOUT)
        assert not consumer.is_alive()

    def test_sat_quit_interrupts_wait(self):
        """Test that SAT quit() properly interrupts wait()"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        # Add a seis to make wait() actually wait
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        update_dt = datetime.now() + timedelta(hours=1)  # Future time
        sat.append(seis, update_dt)

        wait_result = [None]

        def wait_thread():
            wait_result[0] = sat.wait()

        t = threading.Thread(target=wait_thread)
        t.start()

        # Give thread time to start waiting
        time.sleep(0.1)

        # Quit should interrupt
        sat.quit()

        t.join(timeout=TEST_TIMEOUT)
        assert not t.is_alive()
        assert wait_result[0] is False

    def test_sat_wait_returns_false_when_empty(self):
        """Test that SAT wait() returns False immediately when empty"""
        sat = TvDatafeedLive._SeisesAndTrigger()

        start_time = time.time()
        result = sat.wait()
        elapsed = time.time() - start_time

        assert result is False
        assert elapsed < 0.1  # Should return immediately

    @patch('tvDatafeed.TvDatafeed.__init__', return_value=None)
    def test_tvdatafeedlive_destructor_safety(self, mock_init):
        """Test that destructor doesn't raise exceptions"""
        tvl = TvDatafeedLive.__new__(TvDatafeedLive)
        tvl._lock = threading.Lock()
        tvl._thread_lock = threading.Lock()
        tvl._main_thread = None
        tvl._shutdown_in_progress = False
        tvl._sat = TvDatafeedLive._SeisesAndTrigger()

        # Should not raise
        tvl.__del__()

        # Calling again should be safe (idempotent)
        tvl.__del__()


# ============================================================================
# Stress Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.slow
class TestStressTests:
    """High load stress tests for threading"""

    def test_high_volume_consumer_data(self, sample_data):
        """Test consumer under high data volume"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        processed_count = [0]
        lock = threading.Lock()

        def callback(s, data):
            with lock:
                processed_count[0] += 1

        consumer = Consumer(seis, callback)
        consumer.start()

        # Push high volume of data
        for _ in range(STRESS_TEST_ITERATIONS * 5):
            consumer.put(sample_data)

        # Wait for processing
        time.sleep(2.0)

        consumer.stop()
        consumer.join(timeout=TEST_TIMEOUT)

        # Should have processed most data
        assert processed_count[0] > STRESS_TEST_ITERATIONS

    def test_rapid_consumer_creation_destruction(self, sample_data):
        """Test rapid creation and destruction of consumers"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        errors = []

        def create_and_destroy():
            try:
                callback = Mock()
                consumer = Consumer(seis, callback)
                consumer.start()

                consumer.put(sample_data)
                time.sleep(0.01)

                consumer.stop()
                consumer.join(timeout=1.0)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=STRESS_TEST_THREADS) as executor:
            futures = [executor.submit(create_and_destroy)
                      for _ in range(STRESS_TEST_ITERATIONS)]

            for future in as_completed(futures, timeout=TEST_TIMEOUT * 2):
                try:
                    future.result()
                except Exception as e:
                    errors.append(e)

        assert len(errors) == 0, f"Errors: {errors[:5]}..."  # Show first 5 errors

    def test_seis_consumer_churn(self):
        """Test rapid adding/removing of consumers on same Seis"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        errors = []

        def churn():
            try:
                for _ in range(STRESS_TEST_ITERATIONS):
                    consumer = Mock()
                    seis.add_consumer(consumer)
                    # Immediate removal
                    try:
                        seis.pop_consumer(consumer)
                    except NameError:
                        pass
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=churn)
                   for _ in range(STRESS_TEST_THREADS)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT * 2)

        assert len(errors) == 0, f"Errors: {errors}"


# ============================================================================
# Deadlock Detection Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
class TestDeadlockDetection:
    """Tests to detect potential deadlocks with timeouts"""

    def test_nested_lock_consumer_seis(self, sample_data):
        """Test that consumer/seis interactions don't deadlock"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        done = threading.Event()

        def callback(s, data):
            # Try to get consumers while in callback
            consumers = s.get_consumers()
            _ = len(consumers)

        consumer = Consumer(seis, callback)
        seis.add_consumer(consumer)
        consumer.start()

        def interact():
            for _ in range(50):
                # Try to add/remove consumers while callback running
                mock_consumer = Mock()
                seis.add_consumer(mock_consumer)
                time.sleep(0.001)
                try:
                    seis.pop_consumer(mock_consumer)
                except NameError:
                    pass
            done.set()

        # Put data to trigger callback
        for _ in range(20):
            consumer.put(sample_data)

        t = threading.Thread(target=interact)
        t.start()

        # Should complete without deadlock
        finished = done.wait(timeout=TEST_TIMEOUT)

        consumer.stop()
        consumer.join(timeout=TEST_TIMEOUT)
        t.join(timeout=TEST_TIMEOUT)

        assert finished, "Test timed out - possible deadlock"

    def test_sat_operations_no_deadlock(self):
        """Test that SAT operations don't cause deadlocks"""
        sat = TvDatafeedLive._SeisesAndTrigger()
        done = threading.Event()

        def add_remove_seis():
            for i in range(STRESS_TEST_ITERATIONS):
                seis = Seis(f'SYM{i}', 'EXCH', Interval.in_1_hour)
                try:
                    sat.append(seis, datetime.now())
                    time.sleep(0.001)
                    sat.discard(seis)
                except (KeyError, ValueError):
                    pass
            done.set()

        t = threading.Thread(target=add_remove_seis)
        t.start()

        finished = done.wait(timeout=TEST_TIMEOUT * 2)
        t.join(timeout=TEST_TIMEOUT)

        assert finished, "Test timed out - possible deadlock"

    def test_multiple_locks_timeout(self):
        """Test that operations with multiple locks properly timeout"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        # Acquire consumers lock to simulate contention
        seis._consumers_lock.acquire()

        # Operations should still be bounded by timeout
        start_time = time.time()

        def blocked_operation():
            # This will block on the lock
            with seis._consumers_lock:
                pass

        t = threading.Thread(target=blocked_operation)
        t.start()

        # Release lock after short delay
        time.sleep(0.1)
        seis._consumers_lock.release()

        t.join(timeout=TEST_TIMEOUT)
        elapsed = time.time() - start_time

        assert not t.is_alive()
        assert elapsed < TEST_TIMEOUT

    def test_consumer_buffer_timeout(self, sample_data):
        """Test that consumer buffer operations respect timeouts"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        # Create a very slow callback
        def slow_callback(s, data):
            time.sleep(10)  # Very slow

        consumer = Consumer(seis, slow_callback)
        consumer.start()

        # Put should not block indefinitely even with slow callback
        start_time = time.time()

        # Fill buffer rapidly - put has timeout
        for _ in range(100):
            consumer.put(sample_data)
            if time.time() - start_time > TEST_TIMEOUT:
                break

        elapsed = time.time() - start_time

        consumer.stop()
        # Don't wait too long for join since callback is slow
        consumer.join(timeout=1.0)

        assert elapsed < TEST_TIMEOUT, "put() blocked too long"


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
class TestEdgeCases:
    """Edge cases for thread safety"""

    def test_consumer_double_start(self):
        """Test that starting consumer twice doesn't cause issues"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()
        consumer = Consumer(seis, callback)

        consumer.start()

        # Second start should raise RuntimeError (standard Thread behavior)
        with pytest.raises(RuntimeError):
            consumer.start()

        consumer.stop()
        consumer.join(timeout=TEST_TIMEOUT)

    def test_consumer_operations_before_start(self, sample_data):
        """Test consumer operations before start()"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()
        consumer = Consumer(seis, callback)

        # put() before start should not crash
        consumer.put(sample_data)

        # stop() before start should be safe
        consumer.stop()

    def test_seis_operations_after_clear(self):
        """Test Seis operations after all consumers removed"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        # Add and remove consumer
        consumer = Mock()
        seis.add_consumer(consumer)
        seis.pop_consumer(consumer)

        # Should still work
        assert len(seis.get_consumers()) == 0

        # Can add new consumer
        new_consumer = Mock()
        seis.add_consumer(new_consumer)
        assert len(seis.get_consumers()) == 1

    def test_concurrent_repr_and_str(self):
        """Test concurrent access to repr/str methods"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()
        consumer = Consumer(seis, callback)
        consumer.start()

        errors = []

        def call_repr_str():
            try:
                for _ in range(STRESS_TEST_ITERATIONS):
                    _ = repr(consumer)
                    _ = str(consumer)
            except Exception as e:
                errors.append(e)

        def stop_consumer():
            time.sleep(0.01)
            consumer.stop()

        threads = [
            threading.Thread(target=call_repr_str),
            threading.Thread(target=call_repr_str),
            threading.Thread(target=stop_consumer)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=TEST_TIMEOUT)

        consumer.join(timeout=TEST_TIMEOUT)

        assert len(errors) == 0, f"Errors: {errors}"
