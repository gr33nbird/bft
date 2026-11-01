"""BFT coordinator."""

import logging

from datetime import timedelta

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import BFTApi, BFTApiError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BFTCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, api, device_id):

        self.api = api
        self.device_id = device_id
        self.previous_position = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):

        try:
            status = await self.api.execute(
                self.device_id,
                "diagnosis",
            )
            _LOGGER.warning("BFT DIAGNOSE: %s", status)
            first_pos = int(status["first_engine_pos_int"])
            second_pos = int(status["second_engine_pos_int"])

            first_vel = int(status["first_engine_vel_int"])
            second_vel = int(status["second_engine_vel_int"])

            position = (first_pos + second_pos) / 2

            velocity = first_vel + second_vel

            direction = None

            if self.previous_position is not None:
                delta = position - self.previous_position

                if delta > 0:
                    direction = "opening"
                elif delta < 0:
                    direction = "closing"

            self.previous_position = position

            if first_vel != 0 or second_vel != 0:
                state = "moving"

            elif first_pos == 100 and second_pos == 100:
                state = "open"

            elif first_pos == 0 and second_pos == 0:
                state = "closed"

            else:
                state = "stopped"

            return {
                "state": state,
                "position": position,
                "direction": direction,
                "velocity": velocity,
                "raw": status,
            }

        except (BFTApiError, KeyError, TypeError, ValueError) as err:
            raise UpdateFailed(
                f"Error communicating with BFT: {err}"
            ) from err
