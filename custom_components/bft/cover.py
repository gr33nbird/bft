"""BFT cover platform."""

import logging

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass,
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        BFTCover(coordinator, entry)
    ])


class BFTCover(CoordinatorEntity, CoverEntity):
    """BFT gate."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = CoverDeviceClass.GATE

    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
    )

    def __init__(self, coordinator, entry):

        super().__init__(coordinator)

        self._attr_unique_id = entry.unique_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": "Tor",
            "manufacturer": "BFT",
            "model": "DEIMOS",
        }

    @property
    def available(self):
        return super().available

    @property
    def is_closed(self):

        if not self.coordinator.data:
            return None

        return self.coordinator.data["state"] == "closed"

    @property
    def is_opening(self):

        data = self.coordinator.data

        return bool(
            data
            and data["state"] == "moving"
            and data["direction"] == "opening"
        )

    @property
    def is_closing(self):

        data = self.coordinator.data

        return bool(
            data
            and data["state"] == "moving"
            and data["direction"] == "closing"
        )

    @property
    def extra_state_attributes(self):

        if not self.coordinator.data:
            return {}

        return {
            "bft_state": self.coordinator.data["state"],
            "position": self.coordinator.data["position"],
            "direction": self.coordinator.data["direction"],
        }

    async def async_open_cover(self, **kwargs):

        await self.coordinator.api.execute(
            self.coordinator.device_id,
            "open",
        )

        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):

        await self.coordinator.api.execute(
            self.coordinator.device_id,
            "close",
        )

        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs):

        await self.coordinator.api.execute(
            self.coordinator.device_id,
            "stop",
        )

        await self.coordinator.async_request_refresh()
