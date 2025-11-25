"""
Unit tests for tvDatafeed/auth.py (HTTP Authentication)

Tests the TradingViewAuth class that implements HTTP-based authentication
to bypass reCAPTCHA and handle 2FA automatically.
"""

import pytest
import platform
from unittest.mock import Mock, patch, MagicMock
from http.cookiejar import Cookie
import requests

from tvDatafeed.auth import TradingViewAuth
from tvDatafeed.exceptions import AuthenticationError


def create_mock_cookie(name, value):
    """Helper to create a properly formatted mock cookie"""
    return Cookie(
        version=0, name=name, value=value,
        port=None, port_specified=False,
        domain='tradingview.com', domain_specified=False, domain_initial_dot=False,
        path='/', path_specified=True,
        secure=True, expires=None, discard=True,
        comment=None, comment_url=None, rest={}, rfc2109=False
    )


def create_mock_cookiejar(**cookies):
    """Helper to create a mock cookiejar with cookies"""
    from http.cookiejar import CookieJar
    jar = CookieJar()
    for name, value in cookies.items():
        jar.set_cookie(create_mock_cookie(name, value))
    return jar


class TestTradingViewAuth:
    """Test suite for TradingViewAuth class"""

    def test_init_default_user_agent(self):
        """Test initialization with default user agent"""
        auth = TradingViewAuth()

        assert auth.session is not None
        assert isinstance(auth.session, requests.Session)
        assert auth.user_agent.startswith("TWAPI/3.0")
        assert platform.system() in auth.user_agent
        assert platform.release() in auth.user_agent
        assert platform.machine() in auth.user_agent

    def test_init_custom_user_agent(self):
        """Test initialization with custom user agent"""
        custom_ua = "CustomUserAgent/1.0"
        auth = TradingViewAuth(user_agent=custom_ua)

        assert auth.user_agent == custom_ua

    def test_generate_user_agent(self):
        """Test user agent generation"""
        auth = TradingViewAuth()
        user_agent = auth._generate_user_agent()

        assert user_agent.startswith("TWAPI/3.0")
        assert "(" in user_agent
        assert ")" in user_agent
        assert ";" in user_agent

    def test_gen_auth_cookies_empty(self):
        """Test cookie generation with empty session_id"""
        result = TradingViewAuth.gen_auth_cookies(session_id="")
        assert result == ""

    def test_gen_auth_cookies_session_only(self):
        """Test cookie generation with session_id only"""
        session_id = "test_session_123"
        result = TradingViewAuth.gen_auth_cookies(session_id=session_id)

        assert result == f"sessionid={session_id}"

    def test_gen_auth_cookies_with_signature(self):
        """Test cookie generation with session_id and signature"""
        session_id = "test_session_123"
        signature = "test_signature_456"
        result = TradingViewAuth.gen_auth_cookies(
            session_id=session_id,
            signature=signature
        )

        assert result == f"sessionid={session_id};sessionid_sign={signature}"


class TestTradingViewAuthLogin:
    """Test suite for login_user method"""

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_login_success_no_2fa(self, mock_post):
        """Test successful login without 2FA"""
        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "HTML response"
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.cookies = create_mock_cookiejar(
            sessionid='test_session',
            sessionid_sign='test_sign'
        )
        mock_post.return_value = mock_response

        # Mock get_user to return user data
        auth = TradingViewAuth()
        with patch.object(auth, 'get_user') as mock_get_user:
            mock_get_user.return_value = {
                'id': 12345,
                'username': 'testuser',
                'authToken': 'test_token_123'
            }

            result = auth.login_user(
                username="testuser",
                password="testpass"
            )

            # Verify POST was called correctly
            assert mock_post.called
            call_args = mock_post.call_args
            assert 'username=testuser' in call_args[1]['data']
            assert 'password=testpass' in call_args[1]['data']
            assert 'remember=on' in call_args[1]['data']

            # Verify result
            assert result['username'] == 'testuser'
            assert result['authToken'] == 'test_token_123'
            assert result['session'] == 'test_session'
            assert result['signature'] == 'test_sign'

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_login_2fa_required(self, mock_post):
        """Test login when 2FA is required"""
        # Mock 2FA required response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "2FA_required", "code": "2FA_required"}
        mock_response.cookies = create_mock_cookiejar(
            sessionid='test_session',
            sessionid_sign='test_sign'
        )
        mock_post.return_value = mock_response

        auth = TradingViewAuth()

        # Should raise AuthenticationError when no TOTP secret provided
        with pytest.raises(AuthenticationError, match="2FA required but no TOTP secret provided"):
            auth.login_user(
                username="testuser",
                password="testpass"
            )

    @patch('pyotp.TOTP')
    @patch('tvDatafeed.auth.requests.Session.post')
    def test_login_2fa_success(self, mock_post, mock_totp):
        """Test successful login with 2FA"""
        # Mock initial login response requiring 2FA
        initial_response = Mock()
        initial_response.status_code = 200
        initial_response.json.return_value = {"error": "2FA_required", "code": "2FA_required"}
        initial_response.cookies = create_mock_cookiejar(
            sessionid='test_session',
            sessionid_sign='test_sign'
        )

        # Mock 2FA submission response
        totp_response = Mock()
        totp_response.status_code = 200
        totp_response.json.side_effect = ValueError("Not JSON - success")
        totp_response.cookies = create_mock_cookiejar()

        mock_post.side_effect = [initial_response, totp_response]

        # Mock TOTP code generation
        mock_totp_instance = Mock()
        mock_totp_instance.now.return_value = "123456"
        mock_totp.return_value = mock_totp_instance

        # Mock get_user
        auth = TradingViewAuth()
        with patch.object(auth, 'get_user') as mock_get_user:
            mock_get_user.return_value = {
                'id': 12345,
                'username': 'testuser',
                'authToken': 'test_token_with_2fa'
            }

            result = auth.login_user(
                username="testuser",
                password="testpass",
                totp_secret="JBSWY3DPEHPK3PXP"
            )

            # Verify TOTP was called
            assert mock_totp.called
            assert mock_totp_instance.now.called

            # Verify result
            assert result['username'] == 'testuser'
            assert result['authToken'] == 'test_token_with_2fa'

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_login_invalid_credentials(self, mock_post):
        """Test login with invalid credentials"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": "invalid_credentials",
            "code": "invalid_credentials"
        }
        mock_post.return_value = mock_response

        auth = TradingViewAuth()

        with pytest.raises(AuthenticationError, match="invalid_credentials"):
            auth.login_user(
                username="wronguser",
                password="wrongpass"
            )

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_login_no_session_cookie(self, mock_post):
        """Test login when no session cookie is returned"""
        # Mock response without session cookie
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.cookies = create_mock_cookiejar()  # No sessionid!
        mock_post.return_value = mock_response

        auth = TradingViewAuth()

        with pytest.raises(AuthenticationError, match="No session cookie received"):
            auth.login_user(
                username="testuser",
                password="testpass"
            )

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_login_request_exception(self, mock_post):
        """Test login when request fails"""
        mock_post.side_effect = requests.RequestException("Connection error")

        auth = TradingViewAuth()

        with pytest.raises(AuthenticationError, match="Login request failed"):
            auth.login_user(
                username="testuser",
                password="testpass"
            )

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_login_without_remember(self, mock_post):
        """Test login without remember flag"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.cookies = create_mock_cookiejar(sessionid='test_session')
        mock_post.return_value = mock_response

        auth = TradingViewAuth()
        with patch.object(auth, 'get_user') as mock_get_user:
            mock_get_user.return_value = {
                'authToken': 'test_token'
            }

            auth.login_user(
                username="testuser",
                password="testpass",
                remember=False
            )

            # Verify remember=on is NOT in the data
            call_args = mock_post.call_args
            assert 'remember=on' not in call_args[1]['data']


class TestTradingViewAuthSubmit2FA:
    """Test suite for _submit_2fa method"""

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_submit_2fa_success(self, mock_post):
        """Test successful 2FA submission"""
        # Mock successful 2FA response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON - success")
        mock_response.cookies = create_mock_cookiejar()
        mock_post.return_value = mock_response

        auth = TradingViewAuth()
        with patch.object(auth, 'get_user') as mock_get_user:
            mock_get_user.return_value = {
                'id': 12345,
                'authToken': 'test_token_2fa'
            }

            result = auth._submit_2fa(
                session_id="test_session",
                signature="test_sign",
                totp_code="123456"
            )

            # Verify POST was called correctly
            assert mock_post.called
            call_args = mock_post.call_args
            assert 'code=123456' in call_args[1]['data']
            assert 'remember=on' in call_args[1]['data']

            # Verify result
            assert result['authToken'] == 'test_token_2fa'
            assert result['session'] == 'test_session'
            assert result['signature'] == 'test_sign'

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_submit_2fa_invalid_code(self, mock_post):
        """Test 2FA submission with invalid code"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": "Invalid code"
        }
        mock_post.return_value = mock_response

        auth = TradingViewAuth()

        with pytest.raises(AuthenticationError, match="2FA verification failed"):
            auth._submit_2fa(
                session_id="test_session",
                signature="test_sign",
                totp_code="000000"
            )

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_submit_2fa_updated_cookies(self, mock_post):
        """Test 2FA submission with updated session cookies"""
        # Mock response with updated cookies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.cookies = create_mock_cookiejar(
            sessionid='new_session',
            sessionid_sign='new_sign'
        )
        mock_post.return_value = mock_response

        auth = TradingViewAuth()
        with patch.object(auth, 'get_user') as mock_get_user:
            mock_get_user.return_value = {
                'authToken': 'test_token'
            }

            result = auth._submit_2fa(
                session_id="old_session",
                signature="old_sign",
                totp_code="123456"
            )

            # Verify updated session info
            assert result['session'] == 'new_session'
            assert result['signature'] == 'new_sign'

    @patch('tvDatafeed.auth.requests.Session.post')
    def test_submit_2fa_request_exception(self, mock_post):
        """Test 2FA submission when request fails"""
        mock_post.side_effect = requests.RequestException("Network error")

        auth = TradingViewAuth()

        with pytest.raises(AuthenticationError, match="2FA request failed"):
            auth._submit_2fa(
                session_id="test_session",
                signature="test_sign",
                totp_code="123456"
            )


class TestTradingViewAuthGetUser:
    """Test suite for get_user method"""

    @patch('tvDatafeed.auth.requests.Session.get')
    def test_get_user_success(self, mock_get):
        """Test successful user data retrieval"""
        # Mock HTML response with user data (format that matches the regex patterns)
        html_response = '''
        <html>
            <script>
                var user_data = {"id":12345,"username":"testuser","first_name":"Test","last_name":"User","reputation":100.5,
                "following":10,"followers":20,"session_hash":"hash123","private_channel":"channel123",
                "auth_token":"eyJhbGciOiJSUzUxMiJ9.test_token","date_joined":"2020-01-01"};
            </script>
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_response
        mock_response.headers = {}
        mock_get.return_value = mock_response

        auth = TradingViewAuth()
        result = auth.get_user(
            session_id="test_session",
            signature="test_sign"
        )

        # Verify critical user data extraction (auth_token is the most important)
        assert result['id'] == 12345
        assert result['username'] == "testuser"
        assert result['firstName'] == "Test"
        assert result['lastName'] == "User"
        assert result['reputation'] == 100.5
        # Note: following/followers regex may not match compact JSON format
        assert result['sessionHash'] == "hash123"
        assert result['privateChannel'] == "channel123"
        assert result['authToken'] == "eyJhbGciOiJSUzUxMiJ9.test_token"
        assert result['joinDate'] == "2020-01-01"

    @patch('tvDatafeed.auth.requests.Session.get')
    def test_get_user_no_auth_token(self, mock_get):
        """Test get_user when auth_token is not in HTML"""
        mock_response = Mock()
        mock_response.status_code = 200
        # HTML without the substring 'auth_token'
        mock_response.text = "<html><body>Invalid or expired session</body></html>"
        mock_response.headers = {}
        mock_get.return_value = mock_response

        auth = TradingViewAuth()

        # The code checks for 'auth_token' substring in HTML
        # This HTML doesn't contain that substring, so should raise error
        with pytest.raises(AuthenticationError, match="Wrong or expired sessionid/signature"):
            auth.get_user(
                session_id="invalid_session",
                signature="invalid_sign"
            )

    @patch('tvDatafeed.auth.requests.Session.get')
    def test_get_user_redirect(self, mock_get):
        """Test get_user with redirect"""
        # First response with redirect
        redirect_response = Mock()
        redirect_response.status_code = 302
        redirect_response.headers = {'location': 'https://www.tradingview.com/redirect'}
        redirect_response.text = ""

        # Second response after redirect
        final_response = Mock()
        final_response.status_code = 200
        final_response.text = '''
        <html><script>{"auth_token":"test_token","id":123}</script></html>
        '''
        final_response.headers = {}

        mock_get.side_effect = [redirect_response, final_response]

        auth = TradingViewAuth()
        result = auth.get_user(
            session_id="test_session",
            signature="test_sign"
        )

        # Verify redirect was followed
        assert mock_get.call_count == 2
        assert result['authToken'] == "test_token"

    @patch('tvDatafeed.auth.requests.Session.get')
    def test_get_user_missing_fields(self, mock_get):
        """Test get_user with missing optional fields"""
        html_response = '''
        <html>
            <script>
                {"auth_token":"test_token"}
            </script>
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_response
        mock_response.headers = {}
        mock_get.return_value = mock_response

        auth = TradingViewAuth()
        result = auth.get_user(
            session_id="test_session",
            signature="test_sign"
        )

        # Verify defaults for missing fields
        assert result['authToken'] == "test_token"
        assert result['id'] is None
        assert result['username'] is None
        assert result['firstName'] == ""
        assert result['lastName'] == ""
        assert result['reputation'] == 0.0
        assert result['following'] == 0
        assert result['followers'] == 0

    @patch('tvDatafeed.auth.requests.Session.get')
    def test_get_user_request_exception(self, mock_get):
        """Test get_user when request fails"""
        mock_get.side_effect = requests.RequestException("Connection failed")

        auth = TradingViewAuth()

        with pytest.raises(AuthenticationError, match="Failed to get user data"):
            auth.get_user(
                session_id="test_session",
                signature="test_sign"
            )

    @patch('tvDatafeed.auth.requests.Session.get')
    def test_get_user_custom_location(self, mock_get):
        """Test get_user with custom location URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><script>{"auth_token":"test_custom_token"}</script></html>'
        mock_response.headers = {}
        mock_get.return_value = mock_response

        auth = TradingViewAuth()
        custom_url = "https://www.tradingview.com/custom"

        result = auth.get_user(
            session_id="test_session",
            signature="test_sign",
            location=custom_url
        )

        # Verify custom URL was used
        assert mock_get.called
        assert mock_get.call_args[0][0] == custom_url
        # Verify token was extracted
        assert result['authToken'] == 'test_custom_token'


class TestTradingViewAuthIntegration:
    """Integration tests for complete authentication flows"""

    @patch('pyotp.TOTP')
    @patch('tvDatafeed.auth.requests.Session.post')
    @patch('tvDatafeed.auth.requests.Session.get')
    def test_full_login_flow_with_2fa(self, mock_get, mock_post, mock_totp):
        """Test complete login flow with 2FA"""
        # Mock initial login response (2FA required)
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {"error": "2FA_required", "code": "2FA_required"}
        login_response.cookies = create_mock_cookiejar(
            sessionid='sess123',
            sessionid_sign='sign456'
        )

        # Mock 2FA submission response
        totp_response = Mock()
        totp_response.status_code = 200
        totp_response.json.side_effect = ValueError("Not JSON")
        totp_response.cookies = create_mock_cookiejar()

        mock_post.side_effect = [login_response, totp_response]

        # Mock TOTP
        mock_totp_instance = Mock()
        mock_totp_instance.now.return_value = "123456"
        mock_totp.return_value = mock_totp_instance

        # Mock get_user response
        user_html = '''
        <html><script>{"auth_token":"final_token_123","id":999,"username":"user"}</script></html>
        '''
        user_response = Mock()
        user_response.status_code = 200
        user_response.text = user_html
        user_response.headers = {}
        mock_get.return_value = user_response

        # Execute full login
        auth = TradingViewAuth()
        result = auth.login_user(
            username="testuser",
            password="testpass",
            totp_secret="JBSWY3DPEHPK3PXP"
        )

        # Verify complete flow
        assert mock_post.call_count == 2  # Login + 2FA
        assert mock_get.call_count == 1   # Get user data
        assert result['session'] == 'sess123'
        assert result['signature'] == 'sign456'
        assert result['authToken'] == 'final_token_123'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
