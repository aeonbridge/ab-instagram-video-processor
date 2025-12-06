"""
OAuth 2.0 Manager
Handles OAuth 2.0 authentication flow for social media platforms
"""

import json
import webbrowser
import http.server
import socketserver
import urllib.parse
from pathlib import Path
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
import threading
import logging
import time

logger = logging.getLogger(__name__)


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for OAuth callback"""

    auth_code = None
    auth_error = None

    def do_GET(self):
        """Handle GET request with OAuth callback"""
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        # Get authorization code or error
        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            message = "Authorization successful! You can close this window."
            status = 200
        elif 'error' in params:
            OAuthCallbackHandler.auth_error = params['error'][0]
            message = f"Authorization failed: {OAuthCallbackHandler.auth_error}"
            status = 400
        else:
            message = "Invalid callback"
            status = 400

        # Send response
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        html = f"""
        <html>
        <head><title>OAuth Callback</title></head>
        <body>
            <h1>{message}</h1>
            <p>This window will close automatically...</p>
            <script>setTimeout(function(){{ window.close(); }}, 3000);</script>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


class OAuthManager:
    """Manages OAuth 2.0 authentication and token refresh"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080",
        token_file: Optional[Path] = None
    ):
        """
        Initialize OAuth manager

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI for callback
            token_file: Optional path to store tokens
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_file = token_file or Path.home() / '.ab_publisher_tokens.json'

        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.scopes = []

        # Load existing tokens if available
        self.load_tokens()

    def authorize(
        self,
        auth_url: str,
        token_url: str,
        scopes: list,
        **extra_params
    ) -> bool:
        """
        Perform OAuth 2.0 authorization flow

        Args:
            auth_url: Authorization endpoint URL
            token_url: Token endpoint URL
            scopes: List of OAuth scopes
            **extra_params: Extra parameters for auth request

        Returns:
            True if authorization successful
        """
        self.scopes = scopes

        # Build authorization URL
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scopes),
            'access_type': 'offline',  # Get refresh token
            **extra_params
        }

        auth_request_url = f"{auth_url}?{urllib.parse.urlencode(params)}"

        logger.info("Opening browser for authorization...")
        print(f"\nOpening browser for authorization...")
        print(f"If the browser doesn't open, visit this URL:\n{auth_request_url}\n")

        # Start local server for callback
        # Extract port from redirect_uri (e.g., "http://localhost:8080/callback" -> 8080)
        uri_parts = self.redirect_uri.split(':')
        if len(uri_parts) >= 3:
            # Format: http://localhost:8080/... -> split by '/' to get port
            port = int(uri_parts[-1].split('/')[0])
        else:
            port = 8080  # Default port

        auth_code = self._start_callback_server(port, auth_request_url)

        if not auth_code:
            logger.error("Authorization failed")
            return False

        # Exchange authorization code for tokens
        logger.info("Exchanging authorization code for tokens...")
        success = self._exchange_code_for_tokens(auth_code, token_url)

        if success:
            logger.info("Authorization successful!")
            self.save_tokens()

        return success

    def _start_callback_server(self, port: int, auth_url: str = None, timeout: int = 300) -> Optional[str]:
        """
        Start local HTTP server to receive OAuth callback

        Args:
            port: Port to listen on
            auth_url: Full authorization URL to open in browser
            timeout: Timeout in seconds

        Returns:
            Authorization code or None
        """
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.auth_error = None

        # Open browser if URL provided
        if auth_url:
            webbrowser.open(auth_url)

        # Start server in separate thread
        with socketserver.TCPServer(("", port), OAuthCallbackHandler) as httpd:
            logger.info(f"Waiting for OAuth callback on port {port}...")

            # Poll for auth code with timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                httpd.handle_request()

                if OAuthCallbackHandler.auth_code:
                    return OAuthCallbackHandler.auth_code
                elif OAuthCallbackHandler.auth_error:
                    logger.error(f"OAuth error: {OAuthCallbackHandler.auth_error}")
                    return None

                time.sleep(0.1)

            logger.error("OAuth callback timeout")
            return None

    def _get_full_auth_url(self) -> str:
        """Get full authorization URL (implemented by subclasses)"""
        raise NotImplementedError("Must be implemented by platform-specific class")

    def _exchange_code_for_tokens(self, auth_code: str, token_url: str) -> bool:
        """
        Exchange authorization code for access/refresh tokens

        Args:
            auth_code: Authorization code from callback
            token_url: Token endpoint URL

        Returns:
            True if successful
        """
        import requests

        data = {
            'code': auth_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }

        try:
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            self._update_tokens(token_data)
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            return False

    def refresh_access_token(self, token_url: str) -> bool:
        """
        Refresh access token using refresh token

        Args:
            token_url: Token endpoint URL

        Returns:
            True if successful
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False

        import requests

        data = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token'
        }

        try:
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            self._update_tokens(token_data)
            self.save_tokens()

            logger.info("Access token refreshed successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh failed: {e}")
            return False

    def _update_tokens(self, token_data: Dict):
        """Update tokens from API response"""
        self.access_token = token_data.get('access_token')

        # Refresh token might not be returned every time
        if 'refresh_token' in token_data:
            self.refresh_token = token_data['refresh_token']

        # Calculate expiry time
        expires_in = token_data.get('expires_in', 3600)
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

    def is_token_valid(self, buffer_seconds: int = 300) -> bool:
        """
        Check if access token is valid

        Args:
            buffer_seconds: Refresh if expiring within this time

        Returns:
            True if token is valid
        """
        if not self.access_token:
            return False

        if not self.token_expiry:
            return True  # No expiry info, assume valid

        buffer_time = datetime.now() + timedelta(seconds=buffer_seconds)
        return self.token_expiry > buffer_time

    def get_access_token(self, auto_refresh: bool = True, token_url: Optional[str] = None) -> Optional[str]:
        """
        Get valid access token, refreshing if necessary

        Args:
            auto_refresh: Automatically refresh if expired
            token_url: Token URL for refresh

        Returns:
            Valid access token or None
        """
        if self.is_token_valid():
            return self.access_token

        if auto_refresh and self.refresh_token and token_url:
            logger.info("Access token expired, refreshing...")
            if self.refresh_access_token(token_url):
                return self.access_token

        return None

    def save_tokens(self, platform: str = "default"):
        """
        Save tokens to file

        Args:
            platform: Platform identifier for multiple accounts
        """
        if not self.token_file:
            return

        # Load existing tokens
        tokens = {}
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing tokens: {e}")

        # Update platform tokens
        tokens[platform] = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None,
            'scopes': self.scopes,
            'client_id': self.client_id,
        }

        # Save to file
        try:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            logger.info(f"Tokens saved to {self.token_file}")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    def load_tokens(self, platform: str = "default") -> bool:
        """
        Load tokens from file

        Args:
            platform: Platform identifier

        Returns:
            True if tokens loaded
        """
        if not self.token_file or not self.token_file.exists():
            return False

        try:
            with open(self.token_file, 'r') as f:
                tokens = json.load(f)

            if platform not in tokens:
                return False

            platform_tokens = tokens[platform]
            self.access_token = platform_tokens.get('access_token')
            self.refresh_token = platform_tokens.get('refresh_token')
            self.scopes = platform_tokens.get('scopes', [])

            expiry_str = platform_tokens.get('token_expiry')
            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)

            logger.info(f"Tokens loaded from {self.token_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return False

    def revoke_tokens(self, revoke_url: Optional[str] = None):
        """
        Revoke OAuth tokens

        Args:
            revoke_url: Platform revoke endpoint
        """
        if revoke_url and self.access_token:
            import requests
            try:
                requests.post(
                    revoke_url,
                    data={'token': self.access_token},
                    timeout=10
                )
                logger.info("Tokens revoked")
            except Exception as e:
                logger.warning(f"Failed to revoke tokens: {e}")

        # Clear local tokens
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
