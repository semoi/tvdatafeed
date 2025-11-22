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
        mock_tvl = Mock()
        seis.tvdatafeed = mock_tvl

        def bad_callback(s, data):
            raise ValueError("Test exception")

        consumer = Consumer(seis, bad_callback)
        consumer.start()

        # Put data that will cause exception
        consumer.put(sample_ohlcv_data)

        # Wait for processing
        time.sleep(0.1)

        # Consumer should have stopped due to exception
        consumer.join(timeout=1.0)

        # Verify consumer cleaned up
        assert consumer.seis is None
        assert consumer.callback is None
