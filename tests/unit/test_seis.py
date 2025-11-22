"""
Unit tests for Seis class
"""
import pytest
import pandas as pd
from tvDatafeed import Seis, Interval, TvDatafeedLive
from unittest.mock import Mock


@pytest.mark.unit
class TestSeis:
    """Test Seis class"""

    def test_seis_creation(self):
        """Test Seis object creation"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        assert seis.symbol == 'BTCUSDT'
        assert seis.exchange == 'BINANCE'
        assert seis.interval == Interval.in_1_hour

    def test_seis_equality(self):
        """Test Seis equality comparison"""
        seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis2 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        seis3 = Seis('ETHUSDT', 'BINANCE', Interval.in_1_hour)

        assert seis1 == seis2
        assert seis1 != seis3

    def test_seis_repr(self):
        """Test Seis string representation"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        repr_str = repr(seis)
        assert 'BTCUSDT' in repr_str
        assert 'BINANCE' in repr_str

    def test_seis_str(self):
        """Test Seis string format"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        str_repr = str(seis)
        assert 'symbol=' in str_repr
        assert 'BTCUSDT' in str_repr
        assert 'exchange=' in str_repr
        assert 'BINANCE' in str_repr

    def test_seis_properties_readonly(self):
        """Test that symbol, exchange, interval are read-only"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        with pytest.raises(AttributeError):
            seis.symbol = 'ETHUSDT'

        with pytest.raises(AttributeError):
            seis.exchange = 'COINBASE'

        with pytest.raises(AttributeError):
            seis.interval = Interval.in_15_minute

    def test_seis_tvdatafeed_setter(self):
        """Test setting tvdatafeed reference"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        mock_tvl = Mock(spec=TvDatafeedLive)

        seis.tvdatafeed = mock_tvl
        assert seis.tvdatafeed == mock_tvl

    def test_seis_tvdatafeed_cannot_overwrite(self):
        """Test that tvdatafeed cannot be overwritten"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        mock_tvl = Mock(spec=TvDatafeedLive)

        seis.tvdatafeed = mock_tvl

        with pytest.raises(AttributeError, match="Cannot overwrite"):
            seis.tvdatafeed = Mock(spec=TvDatafeedLive)

    def test_seis_tvdatafeed_invalid_type(self):
        """Test that tvdatafeed must be TvDatafeedLive instance"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        with pytest.raises(ValueError, match="must be instance"):
            seis.tvdatafeed = "invalid"

    def test_seis_add_consumer(self):
        """Test adding consumer to Seis"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        mock_consumer = Mock()

        seis.add_consumer(mock_consumer)

        consumers = seis.get_consumers()
        assert mock_consumer in consumers
        assert len(consumers) == 1

    def test_seis_pop_consumer(self):
        """Test removing consumer from Seis"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        mock_consumer = Mock()

        seis.add_consumer(mock_consumer)
        seis.pop_consumer(mock_consumer)

        consumers = seis.get_consumers()
        assert mock_consumer not in consumers
        assert len(consumers) == 0

    def test_seis_pop_nonexistent_consumer(self):
        """Test removing non-existent consumer raises error"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
        mock_consumer = Mock()

        with pytest.raises(NameError, match="does not exist"):
            seis.pop_consumer(mock_consumer)

    def test_seis_is_new_data(self, sample_ohlcv_data):
        """Test is_new_data detection"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        # First call should return True (new data)
        assert seis.is_new_data(sample_ohlcv_data) is True

        # Second call with same data should return False
        assert seis.is_new_data(sample_ohlcv_data) is False

        # Call with different data should return True
        new_data = sample_ohlcv_data.copy()
        new_data.index = new_data.index + pd.Timedelta(hours=1)
        assert seis.is_new_data(new_data) is True

    def test_seis_methods_without_tvdatafeed(self):
        """Test that methods requiring tvdatafeed raise NameError"""
        seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

        with pytest.raises(NameError, match="not provided"):
            seis.get_hist()

        with pytest.raises(NameError, match="not provided"):
            seis.new_consumer(lambda s, d: None)

        with pytest.raises(NameError, match="not provided"):
            seis.del_consumer(Mock())

        with pytest.raises(NameError, match="not provided"):
            seis.del_seis()
