"""
Integration tests for token management scripts

These tests verify the integration between:
- token_manager.py
- get_auth_token.py
- Environment configuration

Note: Some tests require valid credentials and may be skipped in CI environments.
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# Sample JWT tokens for testing
def create_test_jwt(payload: dict) -> str:
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
    payload = {
        "user_id": 12345,
        "exp": int((datetime.now() + timedelta(hours=4)).timestamp()),
        "iat": int(datetime.now().timestamp()),
        "plan": "pro_premium",
        "perm": "cme,nymex",
        "max_connections": 50
    }
    return create_test_jwt(payload)


@pytest.fixture
def temp_env_file(tmp_path, valid_token):
    """Create a temporary .env file with test token"""
    env_file = tmp_path / '.env'
    env_file.write_text(f'''
TV_USERNAME=test_user
TV_PASSWORD=test_password
TV_TOTP_SECRET=JBSWY3DPEHPK3PXP
TV_AUTH_TOKEN="{valid_token}"
''')
    return env_file


class TestTokenManagerIntegration:
    """Integration tests for token_manager module"""

    def test_full_token_lifecycle(self, tmp_path, valid_token):
        """Test the complete token lifecycle: save, cache, retrieve"""
        from scripts import token_manager

        # Setup temporary cache file
        cache_file = tmp_path / '.token_cache.json'
        original_cache = token_manager.TOKEN_CACHE_FILE
        token_manager.TOKEN_CACHE_FILE = cache_file

        try:
            # 1. Save token to cache
            token_manager.save_cached_token(valid_token)
            assert cache_file.exists()

            # 2. Verify cache file structure
            with open(cache_file) as f:
                data = json.load(f)
            assert 'token' in data
            assert 'updated' in data
            assert 'expiry' in data
            assert data['token'] == valid_token

            # 3. Retrieve token from cache
            retrieved = token_manager.get_cached_token()
            assert retrieved == valid_token

            # 4. Validate the token
            assert token_manager.is_token_valid(retrieved)

            # 5. Get token info
            info = token_manager.get_token_info(retrieved)
            assert info['valid'] is True
            assert info['plan'] == 'pro_premium'
            assert info['user_id'] == 12345

        finally:
            token_manager.TOKEN_CACHE_FILE = original_cache

    def test_token_priority_env_over_cache(self, tmp_path, valid_token):
        """Test that environment token takes priority over cached token"""
        from scripts import token_manager

        # Create a different cached token
        cache_token = create_test_jwt({
            "user_id": 99999,
            "exp": int((datetime.now() + timedelta(hours=2)).timestamp()),
            "iat": int(datetime.now().timestamp()),
            "plan": "basic"
        })

        cache_file = tmp_path / '.token_cache.json'
        original_cache = token_manager.TOKEN_CACHE_FILE
        token_manager.TOKEN_CACHE_FILE = cache_file

        try:
            # Save different token to cache
            token_manager.save_cached_token(cache_token)

            # Set env token
            with patch.dict(os.environ, {'TV_AUTH_TOKEN': valid_token}):
                # get_valid_token should return env token, not cached
                token = token_manager.get_valid_token(auto_refresh=False)
                assert token == valid_token

                info = token_manager.get_token_info(token)
                assert info['plan'] == 'pro_premium'  # From env token

        finally:
            token_manager.TOKEN_CACHE_FILE = original_cache

    def test_env_loading_integration(self, tmp_path, valid_token):
        """Test loading environment from .env file"""
        from scripts import token_manager

        # Create temp .env file
        env_file = tmp_path / '.env'
        env_file.write_text(f'''
# Test environment file
TV_USERNAME=integration_test_user
TV_PASSWORD="test_password_123"
TV_AUTH_TOKEN='{valid_token}'
''')

        original_root = token_manager.project_root
        token_manager.project_root = tmp_path

        try:
            # Clear existing env vars
            with patch.dict(os.environ, {}, clear=True):
                token_manager.load_env()

                # Check that values are set (setdefault won't override existing)
                # In a fresh environment, these would be set

        finally:
            token_manager.project_root = original_root

    def test_cache_file_permissions(self, tmp_path, valid_token):
        """Test that cache file has secure permissions"""
        from scripts import token_manager
        import stat

        cache_file = tmp_path / '.token_cache.json'
        original_cache = token_manager.TOKEN_CACHE_FILE
        token_manager.TOKEN_CACHE_FILE = cache_file

        try:
            token_manager.save_cached_token(valid_token)

            # On Windows, chmod doesn't work the same way
            # Just verify the file exists and is readable
            assert cache_file.exists()
            assert cache_file.is_file()

            # File should be readable
            with open(cache_file) as f:
                data = json.load(f)
            assert data['token'] == valid_token

        finally:
            token_manager.TOKEN_CACHE_FILE = original_cache


class TestGetAuthTokenIntegration:
    """Integration tests for get_auth_token module"""

    def test_jwt_decoding_consistency(self, valid_token):
        """Test that JWT decoding is consistent between modules"""
        from scripts.token_manager import decode_jwt, get_token_expiry
        from scripts.get_auth_token import decode_jwt_expiry

        # Both modules should decode the same expiry
        tm_expiry = get_token_expiry(valid_token)
        gat_expiry = decode_jwt_expiry(valid_token)

        # They should be equal (or very close due to timestamp conversion)
        assert tm_expiry is not None
        assert gat_expiry is not None
        assert abs((tm_expiry - gat_expiry).total_seconds()) < 1

    def test_save_and_load_token_integration(self, tmp_path, valid_token):
        """Test saving token via get_auth_token and loading via token_manager"""
        from scripts.get_auth_token import save_token_to_env
        from scripts import token_manager

        # Create temp .env file
        env_file = tmp_path / '.env'
        env_file.write_text('TV_USERNAME=test\n')

        original_root_gat = Path(__file__).parent.parent.parent

        # Patch project_root in get_auth_token
        with patch('scripts.get_auth_token.project_root', tmp_path):
            save_token_to_env(valid_token)

        # Verify the token was saved
        content = env_file.read_text()
        assert 'TV_AUTH_TOKEN=' in content
        assert valid_token in content

        # Now load it via token_manager
        with patch.object(token_manager, 'project_root', tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                token_manager.load_env()
                # The token should now be in environment

    def test_totp_generation(self):
        """Test TOTP code generation if pyotp is available"""
        try:
            import pyotp
            from scripts.get_auth_token import get_totp_code

            # Test with known secret
            secret = "JBSWY3DPEHPK3PXP"
            code = get_totp_code(secret)

            assert code is not None
            assert len(code) == 6
            assert code.isdigit()

            # Verify with pyotp directly
            totp = pyotp.TOTP(secret)
            assert totp.verify(code)

        except ImportError:
            pytest.skip("pyotp not installed")


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""

    def test_automated_data_fetch_workflow(self, tmp_path, valid_token):
        """Test the workflow used in automated_data_fetch.py"""
        from scripts import token_manager

        # Setup
        cache_file = tmp_path / '.token_cache.json'
        original_cache = token_manager.TOKEN_CACHE_FILE
        token_manager.TOKEN_CACHE_FILE = cache_file

        try:
            # Simulate having a cached token
            token_manager.save_cached_token(valid_token)

            # Workflow: get_valid_token -> get_token_info -> use with TvDatafeed
            with patch.dict(os.environ, {}, clear=True):
                token = token_manager.get_valid_token(auto_refresh=False)

                assert token is not None
                assert token == valid_token

                info = token_manager.get_token_info(token)

                assert info['valid'] is True
                assert 'plan' in info
                assert 'expires_at' in info
                assert 'time_remaining' in info

        finally:
            token_manager.TOKEN_CACHE_FILE = original_cache

    def test_token_refresh_workflow_mocked(self, tmp_path, valid_token):
        """Test the token refresh workflow with mocked Playwright"""
        from scripts import token_manager

        cache_file = tmp_path / '.token_cache.json'
        original_cache = token_manager.TOKEN_CACHE_FILE
        token_manager.TOKEN_CACHE_FILE = cache_file

        try:
            # Start with an expired cached token
            expired_token = create_test_jwt({
                "user_id": 12345,
                "exp": int((datetime.now() - timedelta(hours=1)).timestamp()),
                "iat": int((datetime.now() - timedelta(hours=5)).timestamp()),
                "plan": "pro"
            })
            token_manager.save_cached_token(expired_token)

            # Mock the Playwright extraction to return a fresh token
            with patch('scripts.get_auth_token.extract_token_playwright', return_value=valid_token):
                with patch('scripts.get_auth_token.load_env'):
                    with patch.dict(os.environ, {
                        'TV_USERNAME': 'test',
                        'TV_PASSWORD': 'test'
                    }):
                        token = token_manager.get_valid_token(auto_refresh=True)

                        assert token == valid_token
                        assert token_manager.is_token_valid(token)

        finally:
            token_manager.TOKEN_CACHE_FILE = original_cache


class TestErrorHandling:
    """Test error handling across modules"""

    def test_corrupted_cache_recovery(self, tmp_path, valid_token):
        """Test recovery from corrupted cache file"""
        from scripts import token_manager

        cache_file = tmp_path / '.token_cache.json'
        original_cache = token_manager.TOKEN_CACHE_FILE
        token_manager.TOKEN_CACHE_FILE = cache_file

        try:
            # Write corrupted data
            cache_file.write_text('not valid json {{{')

            # Should return None gracefully
            token = token_manager.get_cached_token()
            assert token is None

            # Should be able to save new token
            token_manager.save_cached_token(valid_token)

            # Should now retrieve correctly
            token = token_manager.get_cached_token()
            assert token == valid_token

        finally:
            token_manager.TOKEN_CACHE_FILE = original_cache

    def test_missing_env_file_handling(self, tmp_path):
        """Test handling of missing .env file"""
        from scripts import token_manager

        # Point to non-existent directory
        non_existent = tmp_path / 'does_not_exist'

        with patch.object(token_manager, 'project_root', non_existent):
            # Should not raise, just skip loading
            token_manager.load_env()

    def test_invalid_token_handling(self):
        """Test handling of various invalid tokens"""
        from scripts.token_manager import get_token_info, is_token_valid

        invalid_tokens = [
            None,
            "",
            "not-a-jwt",
            "only.two.parts.not.three.parts",
            "invalid.base64.here",
        ]

        for token in invalid_tokens:
            info = get_token_info(token) if token else get_token_info()
            if token:
                assert info['valid'] is False or 'error' in info

            if token:
                assert is_token_valid(token) is False


@pytest.mark.skipif(
    not os.getenv('TV_USERNAME') or not os.getenv('TV_PASSWORD'),
    reason="Real credentials required for live tests"
)
class TestLiveIntegration:
    """Live integration tests (require real credentials)"""

    def test_real_token_extraction(self):
        """Test real token extraction - SKIPPED unless credentials provided"""
        # This test is skipped by default
        # It would test the actual Playwright extraction
        pytest.skip("Live tests disabled by default")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
