"""Implementation of lock module for TP-Link DL100 smart locks."""

from __future__ import annotations

import logging

from ...feature import Feature
from ..smartmodule import SmartModule

_LOGGER = logging.getLogger(__name__)

# lock_status polarity is device-verified and counterintuitive:
#   0 == bolt extended  == LOCKED
#   1 == bolt retracted == UNLOCKED
#   2 UNINITIALIZED, 3 JAM_IN_UNLOCKING, 4 JAM_IN_LOCKING
LOCK_STATUS_LOCKED = 0
LOCK_STATUS_UNLOCKED = 1


class Lock(SmartModule):
    """Implementation of lock module for SMART.TAPOLOCK devices (DL100)."""

    # No component list is exposed by the DL100; depend on the sysinfo key.
    REQUIRED_COMPONENT = None
    SYSINFO_LOOKUP_KEYS = ["lock_status"]

    # Owner (local) path always uses this synthetic user id. Do NOT send
    # tplink_account / access_info / lock_type / unlock_type for the owner.
    SA_USER_ID = "local_1"

    def _initialize_features(self) -> None:
        """Initialize features after the initial update."""
        self._add_feature(
            Feature(
                self._device,
                id="is_locked",
                name="Locked",
                container=self,
                attribute_getter="is_locked",
                icon="mdi:lock",
                category=Feature.Category.Primary,
                type=Feature.Type.BinarySensor,
            )
        )

    def query(self) -> dict:
        """Query to execute during the update cycle."""
        return {}

    @property
    def is_locked(self) -> bool:
        """Return True when the bolt is extended (lock_status == 0)."""
        return self._device.sys_info["lock_status"] == LOCK_STATUS_LOCKED

    async def lock(self) -> dict:
        """Lock the device (extend the bolt)."""
        return await self._set_lock_status(LOCK_STATUS_LOCKED)

    async def unlock(self) -> dict:
        """Unlock the device (retract the bolt)."""
        return await self._set_lock_status(LOCK_STATUS_UNLOCKED)

    async def _set_lock_status(self, status: int) -> dict:
        """Send setLockStatus for the owner (local) path.

        SmartProtocol wraps this into the multipleRequest envelope the device
        expects, so we only supply the method name and params here.
        """
        return await self.call(
            "setLockStatus",
            {"lock_status": status, "sa_user_id": self.SA_USER_ID},
        )
