"""
Unit tests for Consumer class
"""
import pytest
import time
import threading
from tvDatafeed import Consumer, Seis, Interval
from unittest.mock import Mock
import pandas as pd


@pytest.mark.unit
class TestConsumer:
    """Test Consumer class"""

    def test_consumer_creation(self):
        """Test Consumer object creation"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        consumer = Consumer(seis, callback)

        assert consumer.seis == seis
        assert consumer.callback == callback
        assert 'BTCUSDT' in consumer.name
        assert 'BINANCE' in consumer.name

    def test_consumer_repr(self):
        """Test Consumer string representation"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        def test_callback(s, d):
            pass

        consumer = Consumer(seis, test_callback)
        repr_str = repr(consumer)

        assert 'Consumer' in repr_str
        assert 'test_callback' in repr_str

    def test_consumer_str(self):
        """Test Consumer string format"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        def test_callback(s, d):
            pass

        consumer = Consumer(seis, test_callback)
        str_repr = str(consumer)

        assert 'callback=' in str_repr
        assert 'test_callback' in str_repr

    @pytest.mark.threading
    def test_consumer_put_and_process(self, sample_ohlcv_data):
        """Test putting data and processing via callback"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        received_data = []

        def callback(s, data):
            received_data.append(data)

        consumer = Consumer(seis, callback)
        consumer.start()

        # Put data
        consumer.put(sample_ohlcv_data)

        # Wait for processing
        time.sleep(0.1)

        # Stop consumer
        consumer.stop()
        consumer.join(timeout=1.0)

        # Verify callback was called
        assert len(received_data) == 1
        assert received_data[0] is sample_ohlcv_data

    @pytest.mark.threading
    def test_consumer_multiple_data(self, sample_ohlcv_data):
        """Test processing multiple data batches"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        received_count = [0]  # Use list for mutable closure

        def callback(s, data):
            received_count[0] += 1

        consumer = Consumer(seis, callback)
        consumer.start()

        # Put multiple data
        for _ in range(5):
            consumer.put(sample_ohlcv_data)

        # Wait for processing
        time.sleep(0.2)

        # Stop consumer
        consumer.stop()
        consumer.join(timeout=1.0)

        # Verify all data processed
        assert received_count[0] == 5

    @pytest.mark.threading
    def test_consumer_stop(self):
        """Test consumer stop mechanism"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        consumer = Consumer(seis, callback)
        consumer.start()

        assert consumer.is_alive()

        consumer.stop()
        consumer.join(timeout=1.0)

        assert not consumer.is_alive()

    @pytest.mark.threading
    def test_consumer_exception_handling(self, sample_ohlcv_data):
        """Test that consumer handles callback exceptions"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        # Note: We don't set seis.tvdatafeed because the setter requires
        # a TvDatafeedLive instance. The del_consumer will raise NameError
        # which is caught and logged, then the finally block cleans up.

        def bad_callback(s, data):
            raise ValueError("Test exception")

        consumer = Consumer(seis, bad_callback)
        consumer.start()

        # Put data that will cause exception
        consumer.put(sample_ohlcv_data)

        # Wait for processing and cleanup
        time.sleep(0.2)

        # Consumer should have stopped due to exception
        consumer.join(timeout=2.0)

        # Verify consumer cleaned up (finally block sets these to None)
        assert consumer.seis is None
        assert consumer.callback is None

    def test_consumer_seis_setter(self):
        """Test the seis property setter"""
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis2 = Seis('ETHUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        consumer = Consumer(seis1, callback)
        assert consumer.seis == seis1

        # Test setter
        consumer.seis = seis2
        assert consumer.seis == seis2

        # Test setting to None
        consumer.seis = None
        assert consumer.seis is None

    def test_consumer_callback_setter(self):
        """Test the callback property setter"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback1 = Mock()
        callback2 = Mock()

        consumer = Consumer(seis, callback1)
        assert consumer.callback == callback1

        # Test setter
        consumer.callback = callback2
        assert consumer.callback == callback2

        # Test setting to None
        consumer.callback = None
        assert consumer.callback is None

    def test_consumer_repr_stopped(self):
        """Test Consumer repr when stopped"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        consumer = Consumer(seis, callback)
        # Manually set to None to simulate stopped state
        consumer.seis = None
        consumer.callback = None

        repr_str = repr(consumer)
        assert 'stopped' in repr_str

    def test_consumer_str_stopped(self):
        """Test Consumer str when stopped"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        consumer = Consumer(seis, callback)
        # Manually set to None to simulate stopped state
        consumer.seis = None

        str_repr = str(consumer)
        assert 'stopped' in str_repr

    @pytest.mark.threading
    def test_consumer_put_when_stopped(self, sample_ohlcv_data):
        """Test that put does nothing when consumer is stopped"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        consumer = Consumer(seis, callback)
        # Stop without starting
        consumer.stop()

        # Put data should not raise but also not queue
        consumer.put(sample_ohlcv_data)

        # Buffer should still be empty or only have None
        assert consumer._buffer.qsize() <= 1

    def test_consumer_del_consumer_when_seis_none(self):
        """Test del_consumer when seis is already None"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        callback = Mock()

        consumer = Consumer(seis, callback)
        consumer.seis = None

        # Should return True without error
        result = consumer.del_consumer()
        assert result is True
