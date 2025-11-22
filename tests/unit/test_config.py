"""
Unit tests for config module
"""
import pytest
import os
from tvDatafeed.config import (
    NetworkConfig,
    AuthConfig,
    DataConfig,
    ThreadingConfig,
    TvDatafeedConfig,
    DEFAULT_CONFIG
)


@pytest.mark.unit
class TestNetworkConfig:
    """Test NetworkConfig class"""

    def test_network_config_defaults(self):
        """Test NetworkConfig default values"""
        config = NetworkConfig()

        assert config.ws_url == "wss://data.tradingview.com/socket.io/websocket"
        assert config.connect_timeout == 10.0
        assert config.send_timeout == 5.0
        assert config.recv_timeout == 30.0
        assert config.max_retries == 3
        assert config.base_retry_delay == 2.0
        assert config.max_retry_delay == 60.0
        assert config.requests_per_minute == 60

    def test_network_config_from_env(self, monkeypatch):
        """Test NetworkConfig.from_env()"""
        monkeypatch.setenv('TV_WS_URL', 'wss://custom.url/ws')
        monkeypatch.setenv('TV_CONNECT_TIMEOUT', '20.0')
        monkeypatch.setenv('TV_SEND_TIMEOUT', '10.0')
        monkeypatch.setenv('TV_RECV_TIMEOUT', '60.0')
        monkeypatch.setenv('TV_MAX_RETRIES', '5')
        monkeypatch.setenv('TV_BASE_RETRY_DELAY', '5.0')
        monkeypatch.setenv('TV_MAX_RETRY_DELAY', '120.0')
        monkeypatch.setenv('TV_REQUESTS_PER_MINUTE', '30')

        config = NetworkConfig.from_env()

        assert config.ws_url == 'wss://custom.url/ws'
        assert config.connect_timeout == 20.0
        assert config.send_timeout == 10.0
        assert config.recv_timeout == 60.0
        assert config.max_retries == 5
        assert config.base_retry_delay == 5.0
        assert config.max_retry_delay == 120.0
        assert config.requests_per_minute == 30


@pytest.mark.unit
class TestAuthConfig:
    """Test AuthConfig class"""

    def test_auth_config_defaults(self):
        """Test AuthConfig default values"""
        config = AuthConfig()

        assert config.sign_in_url == 'https://www.tradingview.com/accounts/signin/'
        assert config.username is None
        assert config.password is None
        assert config.two_factor_code is None

    def test_auth_config_from_env(self, monkeypatch):
        """Test AuthConfig.from_env()"""
        monkeypatch.setenv('TV_USERNAME', 'testuser')
        monkeypatch.setenv('TV_PASSWORD', 'testpass')
        monkeypatch.setenv('TV_2FA_CODE', '123456')

        config = AuthConfig.from_env()

        assert config.username == 'testuser'
        assert config.password == 'testpass'
        assert config.two_factor_code == '123456'


@pytest.mark.unit
class TestDataConfig:
    """Test DataConfig class"""

    def test_data_config_defaults(self):
        """Test DataConfig default values"""
        config = DataConfig()

        assert config.max_bars == 5000
        assert config.default_bars == 10
        assert config.validate_data is True
        assert config.fill_missing_volume == 'zero'
        assert config.timezone == 'UTC'

    def test_data_config_from_env(self, monkeypatch):
        """Test DataConfig.from_env()"""
        monkeypatch.setenv('TV_MAX_BARS', '1000')
        monkeypatch.setenv('TV_DEFAULT_BARS', '50')
        monkeypatch.setenv('TV_VALIDATE_DATA', 'false')
        monkeypatch.setenv('TV_FILL_MISSING_VOLUME', 'forward')
        monkeypatch.setenv('TV_TIMEZONE', 'America/New_York')

        config = DataConfig.from_env()

        assert config.max_bars == 1000
        assert config.default_bars == 50
        assert config.validate_data is False
        assert config.fill_missing_volume == 'forward'
        assert config.timezone == 'America/New_York'


@pytest.mark.unit
class TestThreadingConfig:
    """Test ThreadingConfig class"""

    def test_threading_config_defaults(self):
        """Test ThreadingConfig default values"""
        config = ThreadingConfig()

        assert config.retry_limit == 50
        assert config.retry_sleep == 0.1
        assert config.shutdown_timeout == 10.0

    def test_threading_config_from_env(self, monkeypatch):
        """Test ThreadingConfig.from_env()"""
        monkeypatch.setenv('TV_RETRY_LIMIT', '100')
        monkeypatch.setenv('TV_RETRY_SLEEP', '0.5')
        monkeypatch.setenv('TV_SHUTDOWN_TIMEOUT', '30.0')

        config = ThreadingConfig.from_env()

        assert config.retry_limit == 100
        assert config.retry_sleep == 0.5
        assert config.shutdown_timeout == 30.0


@pytest.mark.unit
class TestTvDatafeedConfig:
    """Test TvDatafeedConfig class"""

    def test_tvdatafeed_config_defaults(self):
        """Test TvDatafeedConfig default values"""
        config = TvDatafeedConfig()

        assert isinstance(config.network, NetworkConfig)
        assert isinstance(config.auth, AuthConfig)
        assert isinstance(config.data, DataConfig)
        assert isinstance(config.threading, ThreadingConfig)
        assert config.debug is False

    def test_tvdatafeed_config_from_env(self, monkeypatch):
        """Test TvDatafeedConfig.from_env()"""
        # Set some env variables
        monkeypatch.setenv('TV_USERNAME', 'envuser')
        monkeypatch.setenv('TV_MAX_BARS', '2000')
        monkeypatch.setenv('TV_RETRY_LIMIT', '75')
        monkeypatch.setenv('TV_DEBUG', 'true')

        config = TvDatafeedConfig.from_env()

        assert config.auth.username == 'envuser'
        assert config.data.max_bars == 2000
        assert config.threading.retry_limit == 75
        assert config.debug is True

    def test_tvdatafeed_config_default_factory(self):
        """Test TvDatafeedConfig.default()"""
        config = TvDatafeedConfig.default()

        assert config.debug is False
        assert config.network.max_retries == 3

    def test_default_config_instance(self):
        """Test DEFAULT_CONFIG global instance"""
        assert DEFAULT_CONFIG is not None
        assert isinstance(DEFAULT_CONFIG, TvDatafeedConfig)


@pytest.mark.unit
class TestConfigPartialEnv:
    """Test config with partial environment variables"""

    def test_network_config_partial_env(self, monkeypatch):
        """Test NetworkConfig with only some env vars set"""
        monkeypatch.setenv('TV_MAX_RETRIES', '10')

        config = NetworkConfig.from_env()

        # Custom value from env
        assert config.max_retries == 10
        # Default values for others
        assert config.connect_timeout == 10.0
        assert config.send_timeout == 5.0

    def test_data_config_validate_data_true(self, monkeypatch):
        """Test DataConfig validate_data true value"""
        monkeypatch.setenv('TV_VALIDATE_DATA', 'TRUE')

        config = DataConfig.from_env()
        assert config.validate_data is True

    def test_tvdatafeed_config_debug_false(self, monkeypatch):
        """Test TvDatafeedConfig debug false value"""
        monkeypatch.setenv('TV_DEBUG', 'FALSE')

        config = TvDatafeedConfig.from_env()
        assert config.debug is False
