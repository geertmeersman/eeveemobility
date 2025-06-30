"""EEVEE Mobility library using httpx."""

import logging

from homeassistant.helpers.httpx_client import get_async_client

from .const import API_URL, CLIENT_ID, CLIENT_SECRET, HEADERS, TOKEN_URL, VERSION

_LOGGER = logging.getLogger(__name__)


class EeveeMobilityClient:
    """Class to communicate with the EEVEE Mobility API."""

    def __init__(self, hass, email, password, custom_headers=None):
        """Initialize the EEVEE Mobility Client."""
        self.hass = hass
        self.email = email
        self.password = password
        self.token = None
        self.session = None
        self.custom_headers = custom_headers or {}
        self.client = get_async_client(self.hass)
        _LOGGER.debug("Initialized EeveeMobilityClient for %s", self.email)

    async def _get_token(self, force=False):
        """Obtain the OAuth token."""
        if self.token is None or force:
            _LOGGER.debug("Requesting new token from %s (force=%s)", TOKEN_URL, force)
            try:
                response = await self.client.post(
                    TOKEN_URL,
                    data={
                        "grant_type": "password",
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "email": self.email,
                        "password": self.password,
                        "device_name": f"Home Assistant Eevee Mobility {VERSION}",
                    },
                    headers=self.custom_headers,
                )
                response.raise_for_status()
                self.token = response.json()
                _LOGGER.debug("Token obtained successfully")
            except Exception as e:
                _LOGGER.error("Error retrieving token: %s", str(e))
                raise
        else:
            _LOGGER.debug("Using cached token")
        return self.token.get("access_token")

    async def request(self, path):
        """Send an authorized request to an API endpoint."""
        endpoint_path = f"{API_URL}/{path}"
        _LOGGER.debug("Sending request to %s", endpoint_path)

        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            **HEADERS,
            **self.custom_headers,
        }

        try:
            response = await self.client.get(endpoint_path, headers=headers)
            _LOGGER.debug(
                "Response status from %s: %s", endpoint_path, response.status_code
            )

            if response.status_code == 401:
                _LOGGER.warning("Received 401, refreshing token and retrying request")
                token = await self._get_token(force=True)
                headers["Authorization"] = f"Bearer {token}"
                response = await self.client.get(endpoint_path, headers=headers)
                _LOGGER.debug("Retry response status: %s", response.status_code)

            if response.status_code == 404:
                _LOGGER.debug("Received 404")
                return False

            if response.status_code == 200:
                _LOGGER.debug("Request to %s successful", endpoint_path)
                return response.json()
            else:
                _LOGGER.error(
                    "Request to %s failed with status code %s",
                    endpoint_path,
                    response.status_code,
                )
                raise EeveeAPIException(
                    f"Request to {endpoint_path} failed with status code {response.status_code}"
                )
        except Exception as e:
            _LOGGER.exception(
                "Exception during request to %s: %s", endpoint_path, str(e)
            )
            raise


class EeveeAPIException(Exception):
    """Exception raised for errors in the EEVEE Mobility API."""

    def __init__(self, message):
        """Init EeveeAPIException."""
        super().__init__(message)
        self.message = message
