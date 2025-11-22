"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import sys
from unittest.mock import Mock, MagicMock
import pandas as pd
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tvDatafeed import TvDatafeed, TvDatafeedLive, Interval, Seis, Consumer


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    ws = Mock()
    ws.send = Mock()
    ws.recv = Mock()
    ws.close = Mock()
    ws.ping = Mock()
    ws.gettimeout = Mock(return_value=5.0)
    ws.settimeout = Mock()
    return ws


@pytest.fixture
def mock_auth_response():
    """Mock successful authentication response"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        'user': {
            'auth_token': 'test_token_12345',
            'username': 'testuser'
        }
    }
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV DataFrame"""
    dates = pd.date_range('2021-01-01', periods=10, freq='1H', tz='UTC')
    data = {
        'symbol': ['BTCUSDT'] * 10,
        'open': [30000 + i * 100 for i in range(10)],
        'high': [30100 + i * 100 for i in range(10)],
        'low': [29900 + i * 100 for i in range(10)],
        'close': [30050 + i * 100 for i in range(10)],
        'volume': [1000000 + i * 10000 for i in range(10)]
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'datetime'
    return df


@pytest.fixture
def sample_websocket_message():
    """Sample WebSocket message with timeseries data"""
    return '''~m~500~m~{"m":"timescale_update","p":[1,"s1",{"s":[
        {"i":0,"v":[1609459200,29000.0,29500.0,28500.0,29200.0,15000000.0]},
        {"i":1,"v":[1609462800,29200.0,29800.0,29100.0,29600.0,18000000.0]},
        {"i":2,"v":[1609466400,29600.0,30000.0,29400.0,29800.0,20000000.0]}
    ]}]}~m~'''


@pytest.fixture
def sample_symbol_search_response():
    """Sample symbol search response"""
    return [
        {
            "symbol": "BTCUSDT",
            "description": "Bitcoin / TetherUS",
            "exchange": "BINANCE",
            "type": "crypto"
        },
        {
            "symbol": "ETHUSDT",
            "description": "Ethereum / TetherUS",
            "exchange": "BINANCE",
            "type": "crypto"
        }
    ]


@pytest.fixture
def temp_env_vars(monkeypatch):
    """Set temporary environment variables for testing"""
    monkeypatch.setenv('TV_USERNAME', 'test_user')
    monkeypatch.setenv('TV_PASSWORD', 'test_password')
    monkeypatch.setenv('TV_2FA_CODE', '123456')


@pytest.fixture
def mock_2fa_required_response():
    """Mock response when 2FA is required"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        'two_factor_required': True,
        'two_factor_method': 'totp'
    }
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def mock_2fa_success_response():
    """Mock successful 2FA response"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        'user': {
            'auth_token': 'test_token_2fa_12345',
            'username': 'testuser'
        }
    }
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def mock_2fa_invalid_code_response():
    """Mock 2FA response with invalid code"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        'error': 'Invalid verification code',
        'code': 'invalid_code'
    }
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def valid_totp_secret():
    """A valid TOTP secret for testing"""
    # This is a test secret, not a real one
    return 'JBSWY3DPEHPK3PXP'


# Marks for test categorization
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "network: Tests requiring network access"
    )
    config.addinivalue_line(
        "markers", "threading: Tests involving threading"
    )
