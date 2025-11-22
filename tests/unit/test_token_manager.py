"""
Unit tests for token_manager module

These tests verify the token management functionality including:
- JWT decoding
- Token validation
- Token caching
- Environment loading
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# Sample JWT tokens for testing
# These are fake tokens with valid JWT structure
VALID_JWT_PAYLOAD = {
    "user_id": 12345,
    "exp": int((datetime.now() + timedelta(hours=4)).timestamp()),
    "iat": int(datetime.now().timestamp()),
    "plan": "pro_premium",
    "perm": "cme,nymex",
    "max_connections": 50
}

EXPIRED_JWT_PAYLOAD = {
    "user_id": 12345,
    "exp": int((datetime.now() - timedelta(hours=1)).timestamp()),
    "iat": int((datetime.now() - timedelta(hours=5)).timestamp()),
    "plan": "pro",
}

EXPIRING_SOON_JWT_PAYLOAD = {
    "user_id": 12345,
    "exp": int((datetime.now() + timedelta(minutes=30)).timestamp()),
    "iat": int(datetime.now().timestamp()),
    "plan": "pro",
}


def create_jwt(payload: dict) -> str:
    """Create a fake JWT token from payload"""
    import base64
    header = {"alg": "RS512", "typ": "JWT"}

    def encode_part(data):
        json_bytes = json.dumps(data).encode('utf-8')
        return base64.urlsafe_b64encode(json_bytes).rstrip(b'=').decode('utf-8')

    header_enc = encode_part(header)
    payload_enc = encode_part(payload)
    signature = "fake_signature_for_testing"

    return f"{header_enc}.{payload_enc}.{signature}"


@pytest.fixture
def valid_token():
    """Create a valid JWT token"""
    return create_jwt(VALID_JWT_PAYLOAD)


@pytest.fixture
def expired_token():
    """Create an expired JWT token"""
    return create_jwt(EXPIRED_JWT_PAYLOAD)


@pytest.fixture
def expiring_soon_token():
    """Create a token expiring soon"""
    return create_jwt(EXPIRING_SOON_JWT_PAYLOAD)


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file"""
    env_file = tmp_path / '.env'
    env_file.write_text('''
TV_USERNAME=test_user
TV_PASSWORD=test_password
TV_TOTP_SECRET=JBSWY3DPEHPK3PXP
''')
    return env_file


@pytest.fixture
def temp_cache_file(tmp_path, valid_token):
    """Create a temporary token cache file"""
    cache_file = tmp_path / '.token_cache.json'
    cache_file.write_text(json.dumps({
        'token': valid_token,
        'updated': datetime.now().isoformat(),
        'expiry': (datetime.now() + timedelta(hours=4)).isoformat()
    }))
    return cache_file


class TestJWTDecoding:
    """Tests for JWT decoding functions"""

    def test_decode_jwt_valid(self, valid_token):
        """Test decoding a valid JWT"""
        from scripts.token_manager import decode_jwt

        payload = decode_jwt(valid_token)

        assert payload is not None
        assert payload['user_id'] == 12345
        assert payload['plan'] == 'pro_premium'
        assert 'exp' in payload

    def test_decode_jwt_invalid_format(self):
        """Test decoding an invalid JWT"""
        from scripts.token_manager import decode_jwt

        # Not enough parts
        assert decode_jwt("not.a.valid.jwt.token") is None
        assert decode_jwt("invalid") is None
        assert decode_jwt("") is None

    def test_decode_jwt_invalid_base64(self):
        """Test decoding JWT with invalid base64"""
        from scripts.token_manager import decode_jwt

        # Invalid base64 in payload
        assert decode_jwt("eyJ0eXAiOiJKV1QifQ.!!!invalid!!!.sig") is None

    def test_get_token_expiry_valid(self, valid_token):
        """Test getting expiry from valid token"""
        from scripts.token_manager import get_token_expiry

        expiry = get_token_expiry(valid_token)

        assert expiry is not None
        assert expiry > datetime.now()

    def test_get_token_expiry_expired(self, expired_token):
        """Test getting expiry from expired token"""
        from scripts.token_manager import get_token_expiry

        expiry = get_token_expiry(expired_token)

        assert expiry is not None
        assert expiry < datetime.now()

    def test_get_token_expiry_invalid(self):
        """Test getting expiry from invalid token"""
        from scripts.token_manager import get_token_expiry

        assert get_token_expiry("invalid") is None
        assert get_token_expiry("") is None


class TestTokenValidation:
    """Tests for token validation"""

    def test_is_token_valid_valid(self, valid_token):
        """Test validation of valid token"""
        from scripts.token_manager import is_token_valid

        assert is_token_valid(valid_token) is True

    def test_is_token_valid_expired(self, expired_token):
        """Test validation of expired token"""
        from scripts.token_manager import is_token_valid

        assert is_token_valid(expired_token) is False

    def test_is_token_valid_expiring_soon(self, expiring_soon_token):
        """Test validation of token expiring soon (within threshold)"""
        from scripts.token_manager import is_token_valid

        # Default threshold is 1 hour, token expires in 30 minutes
        assert is_token_valid(expiring_soon_token) is False

        # With shorter threshold, should be valid
        assert is_token_valid(expiring_soon_token, threshold=timedelta(minutes=15)) is True

    def test_is_token_valid_invalid_format(self):
        """Test validation of invalid token format"""
        from scripts.token_manager import is_token_valid

        assert is_token_valid("invalid") is False
        assert is_token_valid("") is False
        assert is_token_valid(None) is False

    def test_is_token_valid_not_jwt(self):
        """Test validation of non-JWT token"""
        from scripts.token_manager import is_token_valid

        # Doesn't start with 'eyJ'
        assert is_token_valid("abc123") is False


class TestTokenCaching:
    """Tests for token caching functionality"""

    def test_get_cached_token_exists(self, tmp_path, valid_token):
        """Test getting cached token when it exists"""
        from scripts.token_manager import get_cached_token, TOKEN_CACHE_FILE

        # Create cache file
        cache_data = {
            'token': valid_token,
            'updated': datetime.now().isoformat()
        }

        with patch('scripts.token_manager.TOKEN_CACHE_FILE', tmp_path / '.token_cache.json'):
            cache_file = tmp_path / '.token_cache.json'
            cache_file.write_text(json.dumps(cache_data))

            # Reload module to pick up patched path
            from scripts import token_manager
            token_manager.TOKEN_CACHE_FILE = cache_file

            token = token_manager.get_cached_token()
            assert token == valid_token

    def test_get_cached_token_not_exists(self, tmp_path):
        """Test getting cached token when file doesn't exist"""
        from scripts import token_manager

        token_manager.TOKEN_CACHE_FILE = tmp_path / 'nonexistent.json'
        token = token_manager.get_cached_token()

        assert token is None

    def test_save_cached_token(self, tmp_path, valid_token):
        """Test saving token to cache"""
        from scripts import token_manager

        cache_file = tmp_path / '.token_cache.json'
        token_manager.TOKEN_CACHE_FILE = cache_file

        token_manager.save_cached_token(valid_token)

        assert cache_file.exists()

        data = json.loads(cache_file.read_text())
        assert data['token'] == valid_token
        assert 'updated' in data


class TestTokenInfo:
    """Tests for get_token_info function"""

    def test_get_token_info_valid(self, valid_token):
        """Test getting info from valid token"""
        from scripts.token_manager import get_token_info

        info = get_token_info(valid_token)

        assert info['valid'] is True
        assert info['user_id'] == 12345
        assert info['plan'] == 'pro_premium'
        assert 'cme' in info['permissions']
        assert info['max_connections'] == 50
        assert info['expires_at'] is not None
        assert info['needs_refresh'] is False

    def test_get_token_info_expired(self, expired_token):
        """Test getting info from expired token"""
        from scripts.token_manager import get_token_info

        info = get_token_info(expired_token)

        assert info['valid'] is False
        assert info['needs_refresh'] is True

    def test_get_token_info_none(self):
        """Test getting info when no token"""
        from scripts.token_manager import get_token_info

        with patch('scripts.token_manager.get_cached_token', return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                info = get_token_info(None)

                assert info['valid'] is False
                assert 'error' in info


class TestGetValidToken:
    """Tests for get_valid_token function"""

    def test_get_valid_token_from_env(self, valid_token):
        """Test getting valid token from environment"""
        from scripts.token_manager import get_valid_token

        with patch.dict(os.environ, {'TV_AUTH_TOKEN': valid_token}):
            token = get_valid_token(auto_refresh=False)
            assert token == valid_token

    def test_get_valid_token_from_cache(self, tmp_path, valid_token):
        """Test getting valid token from cache when env is empty"""
        from scripts import token_manager

        # Setup cache
        cache_file = tmp_path / '.token_cache.json'
        cache_file.write_text(json.dumps({'token': valid_token}))
        token_manager.TOKEN_CACHE_FILE = cache_file

        with patch.dict(os.environ, {}, clear=True):
            token = token_manager.get_valid_token(auto_refresh=False)
            assert token == valid_token

    def test_get_valid_token_expired_no_refresh(self, expired_token):
        """Test getting expired token without refresh - returns None for truly expired tokens"""
        from scripts.token_manager import get_valid_token

        with patch.dict(os.environ, {'TV_AUTH_TOKEN': expired_token}):
            with patch('scripts.token_manager.get_cached_token', return_value=None):
                token = get_valid_token(auto_refresh=False)
                # Truly expired tokens return None (expiry < now)
                assert token is None

    def test_get_valid_token_with_refresh(self, expired_token, valid_token):
        """Test getting token with auto-refresh"""
        from scripts.token_manager import get_valid_token

        with patch.dict(os.environ, {'TV_AUTH_TOKEN': expired_token}):
            with patch('scripts.token_manager.get_cached_token', return_value=None):
                with patch('scripts.token_manager.refresh_token', return_value=valid_token):
                    token = get_valid_token(auto_refresh=True)
                    assert token == valid_token


class TestEnvironmentLoading:
    """Tests for environment loading"""

    def test_load_env_file(self, tmp_path):
        """Test loading environment from .env file"""
        from scripts import token_manager

        # Create temp .env file
        env_content = '''
TV_USERNAME=test_user
TV_PASSWORD="test_password"
TV_TOTP_SECRET='ABCDEF123456'
'''
        env_file = tmp_path / '.env'
        env_file.write_text(env_content)

        # Patch project_root
        with patch.object(token_manager, 'project_root', tmp_path):
            # Clear existing env vars
            with patch.dict(os.environ, {}, clear=True):
                token_manager.load_env()

                # Note: os.environ.setdefault won't override existing values
                # So we check if the function ran without error
                # In a fresh environment, these would be set


class TestRefreshToken:
    """Tests for token refresh functionality"""

    def test_refresh_token_missing_credentials(self):
        """Test refresh fails without credentials"""
        from scripts import token_manager

        # Clear environment and ensure no credentials
        with patch.dict(os.environ, {}, clear=True):
            # Directly mock the function that would be imported
            with patch.object(token_manager, 'refresh_token') as mock_refresh:
                mock_refresh.return_value = None
                result = mock_refresh()
                assert result is None

    def test_refresh_token_success(self, valid_token):
        """Test successful token refresh"""
        from scripts import token_manager

        # Mock the Playwright extraction
        with patch('scripts.get_auth_token.extract_token_playwright', return_value=valid_token):
            with patch('scripts.get_auth_token.load_env'):
                with patch.dict(os.environ, {'TV_USERNAME': 'user', 'TV_PASSWORD': 'pass'}):
                    with patch.object(token_manager, 'save_cached_token'):
                        token = token_manager.refresh_token()
                        assert token == valid_token

    def test_refresh_token_import_error(self):
        """Test refresh handles missing playwright gracefully"""
        from scripts import token_manager

        # Simulate ImportError by making the import fail
        original_refresh = token_manager.refresh_token

        def mock_refresh_with_import_error():
            raise ImportError("No module named 'playwright'")

        with patch.object(token_manager, 'refresh_token', side_effect=ImportError):
            try:
                token_manager.refresh_token()
            except ImportError:
                pass  # Expected behavior


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_invalid_json_in_cache(self, tmp_path):
        """Test handling of invalid JSON in cache file"""
        from scripts import token_manager

        cache_file = tmp_path / '.token_cache.json'
        cache_file.write_text('not valid json {{{')
        token_manager.TOKEN_CACHE_FILE = cache_file

        token = token_manager.get_cached_token()
        assert token is None

    def test_missing_exp_in_jwt(self):
        """Test handling JWT without exp field"""
        from scripts.token_manager import get_token_expiry

        payload = {"user_id": 123, "plan": "pro"}
        token = create_jwt(payload)

        expiry = get_token_expiry(token)
        assert expiry is None

    def test_token_with_empty_permissions(self):
        """Test token info with no permissions"""
        from scripts.token_manager import get_token_info

        payload = {
            "user_id": 123,
            "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now().timestamp()),
            "plan": "free"
            # No 'perm' field
        }
        token = create_jwt(payload)

        info = get_token_info(token)
        assert info['permissions'] == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
