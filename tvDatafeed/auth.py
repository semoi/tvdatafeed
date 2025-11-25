"""
TradingView Authentication Module

This module handles authentication with TradingView using HTTP requests.
It bypasses reCAPTCHA by using simple POST requests instead of browser automation.

Based on the implementation from: https://github.com/dovudo/tradingview-websocket
"""

import re
import platform
import logging
import requests
from typing import Optional, Dict, Any

from .exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class TradingViewAuth:
    """Handle TradingView authentication using HTTP requests"""

    def __init__(self, user_agent: Optional[str] = None):
        """
        Initialize the authentication handler

        Args:
            user_agent: Custom user agent string. If None, generates a default one.
        """
        self.user_agent = user_agent or self._generate_user_agent()
        self.session = requests.Session()

    def _generate_user_agent(self) -> str:
        """Generate a user agent string similar to TradingView API clients"""
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        return f"TWAPI/3.0 ({release}; {system}; {machine})"

    @staticmethod
    def gen_auth_cookies(session_id: str = "", signature: str = "") -> str:
        """
        Generate authentication cookie string

        Args:
            session_id: TradingView session ID
            signature: TradingView session signature

        Returns:
            Cookie string for authentication
        """
        if not session_id:
            return ""
        if not signature:
            return f"sessionid={session_id}"
        return f"sessionid={session_id};sessionid_sign={signature}"

    def _submit_2fa(
        self,
        session_id: str,
        signature: str,
        totp_code: str
    ) -> Dict[str, Any]:
        """
        Submit 2FA TOTP code

        Args:
            session_id: Session ID from initial login
            signature: Session signature from initial login
            totp_code: 6-digit TOTP code

        Returns:
            Dictionary containing user data and session tokens

        Raises:
            AuthenticationError: If 2FA verification fails
        """
        url = "https://www.tradingview.com/accounts/two-factor/signin/totp/"

        # Prepare form data
        data = f"code={totp_code}&remember=on"

        # Prepare headers with session cookies
        headers = {
            "Referer": "https://www.tradingview.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self.user_agent,
            "Cookie": self.gen_auth_cookies(session_id, signature),
        }

        logger.debug(f"Submitting 2FA code to: {url}")

        try:
            response = self.session.post(
                url,
                data=data,
                headers=headers,
                allow_redirects=False
            )

            logger.debug(f"2FA Response status: {response.status_code}")

            # Check for JSON error
            try:
                json_response = response.json()
                if "error" in json_response:
                    error_msg = json_response["error"]
                    logger.error(f"2FA Error: {json_response}")
                    raise AuthenticationError(f"2FA verification failed: {error_msg}")
            except ValueError:
                # HTML response expected for success
                pass

            # Get updated cookies if any
            cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
            if 'sessionid' in cookies_dict:
                session_id = cookies_dict['sessionid']
            if 'sessionid_sign' in cookies_dict:
                signature = cookies_dict['sessionid_sign']

            logger.debug("2FA successful, fetching user data...")

            # Get user data with the authenticated session
            user_data = self.get_user(session_id, signature)

            # Add session info
            user_data['session'] = session_id
            user_data['signature'] = signature

            return user_data

        except requests.RequestException as e:
            logger.error(f"2FA request exception: {e}")
            raise AuthenticationError(f"2FA request failed: {e}")

    def login_user(
        self,
        username: str,
        password: str,
        totp_secret: Optional[str] = None,
        remember: bool = True
    ) -> Dict[str, Any]:
        """
        Login to TradingView using username and password

        Args:
            username: TradingView username/email
            password: TradingView password
            totp_secret: TOTP secret for 2FA (optional)
            remember: Whether to set "remember me" flag

        Returns:
            Dictionary containing user data and session tokens

        Raises:
            AuthenticationError: If login fails
        """
        url = "https://www.tradingview.com/accounts/signin/"

        # Prepare form data
        data = f"username={username}&password={password}"
        if remember:
            data += "&remember=on"

        # Prepare headers
        headers = {
            "Referer": "https://www.tradingview.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self.user_agent,
        }

        logger.debug(f"Attempting login for user: {username}")

        # Make POST request
        try:
            response = self.session.post(
                url,
                data=data,
                headers=headers,
                allow_redirects=False
            )

            logger.debug(f"Response status: {response.status_code}")

            # Check for JSON response (error or 2FA required)
            try:
                json_response = response.json()

                # Check if 2FA is required
                if json_response.get("error") == "2FA_required" or json_response.get("code") == "2FA_required":
                    logger.debug("2FA required")

                    if not totp_secret:
                        raise AuthenticationError("2FA required but no TOTP secret provided")

                    # Extract cookies from response
                    cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
                    session_id = cookies_dict.get('sessionid')
                    signature = cookies_dict.get('sessionid_sign')

                    if not session_id:
                        raise AuthenticationError("No session cookie received for 2FA")

                    logger.debug("Session cookies received, proceeding with 2FA...")

                    # Generate TOTP code
                    try:
                        import pyotp
                        totp = pyotp.TOTP(totp_secret.replace(' ', '').upper())
                        totp_code = totp.now()
                        logger.debug(f"Generated TOTP code: {totp_code}")
                    except ImportError:
                        raise AuthenticationError("pyotp library required for 2FA. Install with: pip install pyotp")

                    # Submit 2FA code
                    return self._submit_2fa(session_id, signature, totp_code)

                # Check for other errors
                if "error" in json_response:
                    error_msg = json_response["error"]
                    error_code = json_response.get("code", "unknown")
                    logger.error(f"Error response: {json_response}")
                    raise AuthenticationError(f"Login failed: {error_msg} (code: {error_code})")

            except ValueError:
                # Not a JSON response, this is expected for successful login without 2FA
                logger.debug("Response is HTML (expected for successful login)")

            # Extract cookies from response
            cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
            session_id = cookies_dict.get('sessionid')
            signature = cookies_dict.get('sessionid_sign', '')

            if not session_id:
                logger.error("No session cookie found in response")
                raise AuthenticationError("Login failed: No session cookie received")

            logger.debug(f"Session ID extracted: {session_id[:20]}...")
            if signature:
                logger.debug(f"Signature extracted: {signature[:20]}...")

            # Get user data using the session
            user_data = self.get_user(session_id, signature)

            # Add session info to user data
            user_data['session'] = session_id
            user_data['signature'] = signature or ''

            return user_data

        except requests.RequestException as e:
            logger.error(f"Request exception: {e}")
            raise AuthenticationError(f"Login request failed: {e}")

    def get_user(
        self,
        session_id: str,
        signature: str = "",
        location: str = "https://www.tradingview.com/"
    ) -> Dict[str, Any]:
        """
        Get user data using session cookies

        Args:
            session_id: TradingView session ID
            signature: TradingView session signature
            location: URL to fetch user data from

        Returns:
            Dictionary containing user data including auth_token

        Raises:
            AuthenticationError: If session is invalid or expired
        """
        logger.debug(f"Getting user data from: {location}")

        headers = {
            "Cookie": self.gen_auth_cookies(session_id, signature),
            "User-Agent": self.user_agent,
        }

        try:
            response = self.session.get(
                location,
                headers=headers,
                allow_redirects=False
            )

            logger.debug(f"Response status: {response.status_code}")

            # Check if we got redirected
            if 'location' in response.headers:
                redirect_url = response.headers['location']
                if redirect_url != location:
                    logger.debug(f"Following redirect to: {redirect_url}")
                    return self.get_user(session_id, signature, redirect_url)

            html = response.text

            # Check if auth_token is present (indicates valid session)
            if 'auth_token' not in html:
                logger.error("No auth_token found in response")
                raise AuthenticationError("Wrong or expired sessionid/signature")

            logger.debug("auth_token found in HTML, extracting user data...")

            # Extract user data using regex patterns (same as JavaScript version)
            user_data = {}

            # Extract user ID
            match = re.search(r'"id":([0-9]{1,10}),', html)
            user_data['id'] = int(match.group(1)) if match else None

            # Extract username
            match = re.search(r'"username":"(.*?)"', html)
            user_data['username'] = match.group(1) if match else None

            # Extract first name
            match = re.search(r'"first_name":"(.*?)"', html)
            user_data['firstName'] = match.group(1) if match else ""

            # Extract last name
            match = re.search(r'"last_name":"(.*?)"', html)
            user_data['lastName'] = match.group(1) if match else ""

            # Extract reputation
            match = re.search(r'"reputation":(.*?),', html)
            user_data['reputation'] = float(match.group(1)) if match else 0.0

            # Extract following count
            match = re.search(r',"following":([0-9]*?),', html)
            user_data['following'] = int(match.group(1)) if match else 0

            # Extract followers count
            match = re.search(r',"followers":([0-9]*?),', html)
            user_data['followers'] = int(match.group(1)) if match else 0

            # Extract session hash
            match = re.search(r'"session_hash":"(.*?)"', html)
            user_data['sessionHash'] = match.group(1) if match else None

            # Extract private channel
            match = re.search(r'"private_channel":"(.*?)"', html)
            user_data['privateChannel'] = match.group(1) if match else None

            # Extract auth token (THIS IS THE KEY!)
            match = re.search(r'"auth_token":"(.*?)"', html)
            user_data['authToken'] = match.group(1) if match else None

            # Extract join date
            match = re.search(r'"date_joined":"(.*?)"', html)
            user_data['joinDate'] = match.group(1) if match else None

            logger.debug(f"User data extracted: ID={user_data.get('id')}, Username={user_data.get('username')}")

            return user_data

        except requests.RequestException as e:
            logger.error(f"Request exception: {e}")
            raise AuthenticationError(f"Failed to get user data: {e}")
