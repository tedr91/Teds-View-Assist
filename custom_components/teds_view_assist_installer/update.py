"""Single bundle Update entity for Ted's View Assist."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TedsVAUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the update entity."""
    coordinator: TedsVAUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TedsVAUpdate(coordinator)])


class TedsVAUpdate(CoordinatorEntity[TedsVAUpdateCoordinator], UpdateEntity):
    """Surfaces a new Teds View Assist release and installs changed assets."""

    _attr_has_entity_name = False
    _attr_name = "Teds View Assist"
    _attr_title = "Ted's View Assist"
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
    )

    def __init__(self, coordinator: TedsVAUpdateCoordinator) -> None:
        """Initialise from the coordinator."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_bundle"

    @property
    def installed_version(self) -> str | None:
        """Release tag currently installed."""
        return self.coordinator.installed_tag

    @property
    def latest_version(self) -> str | None:
        """Latest release tag available."""
        return self.coordinator.latest_tag

    @property
    def release_url(self) -> str | None:
        """Link to the release on GitHub."""
        repo = self.coordinator.github.repo
        if tag := self.coordinator.latest_tag:
            return f"https://github.com/{repo}/releases/tag/{tag}"
        return f"https://github.com/{repo}/releases"

    async def async_release_notes(self) -> str | None:
        """Return the latest release notes."""
        return self.coordinator.release_body or None

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        """Install changed assets up to the latest release."""
        await self.coordinator.async_install_all()
