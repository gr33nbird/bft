"""BFT uControl API."""

import aiohttp
import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_URL, DISPATCHER_URL

_LOGGER = logging.getLogger(__name__)


class BFTApiError(Exception):
    """BFT API error."""


class BFTApi:

    def __init__(self, hass, username, password):
        self.hass = hass
        self.username = username
        self.password = password
        self.session = async_get_clientsession(hass)
        self.access_token = None

    async def login(self):
        """Authenticate with BFT."""

        url = f"{API_URL}/oauth/token"

        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }

        try:
            async with self.session.post(
                url,
                data=data,
                auth=aiohttp.BasicAuth("particle", "particle"),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:

                response.raise_for_status()
                result = await response.json()

                self.access_token = result["access_token"]

                return True

        except (aiohttp.ClientError, KeyError, ValueError) as err:
            raise BFTApiError("BFT login failed") from err

    async def get_devices(self):
        """Retrieve BFT devices."""

        if not self.access_token:
            await self.login()

        url = f"{API_URL}/api/v1/users/"

        try:
            async with self.session.get(
                url,
                params={"access_token": self.access_token},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:

                response.raise_for_status()
                result = await response.json()

                return result["data"]["automations"]

        except (aiohttp.ClientError, KeyError, ValueError) as err:
            raise BFTApiError("Unable to retrieve BFT devices") from err

    async def get_device_id(self, device_name):
        """Find device UUID by name."""

        devices = await self.get_devices()

        for device in devices:
            if device.get("info", {}).get("name") == device_name:
                return device["uuid"]

        raise BFTApiError(
            f"BFT device '{device_name}' not found"
        )

    async def execute(self, device_id, command):
        """Execute a BFT command."""

        if not self.access_token:
            await self.login()

        url = (
            f"{DISPATCHER_URL}/{device_id}/execute/{command}"
        )

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:

                if response.status == 401:
                    await self.login()

                    headers["Authorization"] = (
                        f"Bearer {self.access_token}"
                    )

                    async with self.session.get(
                        url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=20),
                    ) as retry:
                        retry.raise_for_status()
                        return await retry.json()

                response.raise_for_status()
                return await response.json()

        except (aiohttp.ClientError, ValueError) as err:
            raise BFTApiError(
                f"BFT command {command} failed"
            ) from err
