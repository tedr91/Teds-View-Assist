"""Update coordinator for Ted's View Assist Installer."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    STORE_INSTALLED_TAG,
    STORE_VERSIONS,
    UPDATE_CHECK_INTERVAL_HOURS,
)
from .github import GitHubClient, GitHubError
from .installer import Installer

_LOGGER = logging.getLogger(__name__)


class TedsVAUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Poll GitHub for the latest release and run installs."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        github: GitHubClient,
        installer: Installer,
        store: Store,
        data: dict,
    ) -> None:
        """Initialise from persisted install state."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=UPDATE_CHECK_INTERVAL_HOURS),
            config_entry=entry,
        )
        self.github = github
        self.installer = installer
        self.store = store
        self._installed_tag: str | None = data.get(STORE_INSTALLED_TAG)
        self._versions: dict = data.get(STORE_VERSIONS, {})

    @property
    def installed_tag(self) -> str | None:
        """Release tag last installed on this system."""
        return self._installed_tag

    @property
    def latest_tag(self) -> str | None:
        """Latest release tag available in the repo."""
        return (self.data or {}).get("tag")

    @property
    def release_body(self) -> str:
        """Markdown release notes of the latest release."""
        return (self.data or {}).get("body", "")

    async def _async_update_data(self) -> dict:
        try:
            latest = await self.github.async_latest_release()
        except GitHubError as err:
            raise UpdateFailed(str(err)) from err
        if latest is None:
            return {"tag": self._installed_tag, "body": ""}
        tag, body = latest
        return {"tag": tag, "body": body}

    async def async_install_all(self, force: bool = False) -> None:
        """Install/update every changed asset."""
        self._versions = await self.installer.async_install_all(self._versions, force=force)
        await self._record_installed()

    async def async_install_asset(self, asset_class: str, name: str | None = None) -> None:
        """Install a single asset class (optionally one named item)."""
        self._versions = await self.installer.async_install_asset(
            self._versions, asset_class, name
        )
        await self._record_installed()

    async def _record_installed(self) -> None:
        if tag := self.latest_tag:
            self._installed_tag = tag
        await self.store.async_save(
            {STORE_INSTALLED_TAG: self._installed_tag, STORE_VERSIONS: self._versions}
        )
        self.async_update_listeners()
