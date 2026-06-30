"""Ted's View Assist Installer integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import Store

from .const import (
    ASSET_CLASSES,
    ATTR_ASSET_CLASS,
    ATTR_FORCE,
    ATTR_NAME,
    CONF_BRANCH,
    CONF_REPO,
    DEFAULT_BRANCH,
    DEFAULT_REPO,
    DOMAIN,
    SERVICE_CHECK_UPDATES,
    SERVICE_INSTALL_ALL,
    SERVICE_INSTALL_ASSET,
    STORAGE_KEY,
    STORAGE_VERSION,
    STORE_INSTALLED_TAG,
    VA_DOMAIN,
    VA_LOAD_ASSET_SERVICE,
)
from .coordinator import TedsVAUpdateCoordinator
from .github import GitHubClient
from .installer import Installer

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.UPDATE]

_INSTALL_ALL_SCHEMA = vol.Schema({vol.Optional(ATTR_FORCE, default=False): cv.boolean})
_INSTALL_ASSET_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ASSET_CLASS): vol.In(ASSET_CLASSES),
        vol.Optional(ATTR_NAME): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ted's View Assist Installer from a config entry."""
    if not hass.services.has_service(VA_DOMAIN, VA_LOAD_ASSET_SERVICE):
        raise ConfigEntryNotReady(
            "Waiting for View Assist (view_assist.load_asset is unavailable)."
        )

    github = GitHubClient(
        hass,
        entry.options.get(CONF_REPO, DEFAULT_REPO),
        entry.options.get(CONF_BRANCH, DEFAULT_BRANCH),
    )
    installer = Installer(hass, github)
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load() or {}

    coordinator = TedsVAUpdateCoordinator(hass, entry, github, installer, store, data)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)

    if not data.get(STORE_INSTALLED_TAG):
        entry.async_create_background_task(
            hass, _async_first_install(coordinator), f"{DOMAIN}_first_install"
        )

    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_first_install(coordinator: TedsVAUpdateCoordinator) -> None:
    try:
        await coordinator.async_install_all()
    except Exception:  # noqa: BLE001
        _LOGGER.exception(
            "Initial Ted's View Assist install failed; call %s.%s to retry",
            DOMAIN,
            SERVICE_INSTALL_ALL,
        )


@callback
def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_INSTALL_ALL):
        return

    def _coordinator() -> TedsVAUpdateCoordinator:
        return next(iter(hass.data[DOMAIN].values()))

    async def install_all(call: ServiceCall) -> None:
        await _coordinator().async_install_all(force=call.data[ATTR_FORCE])

    async def install_asset(call: ServiceCall) -> None:
        await _coordinator().async_install_asset(
            call.data[ATTR_ASSET_CLASS], call.data.get(ATTR_NAME)
        )

    async def check_updates(call: ServiceCall) -> None:
        await _coordinator().async_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_INSTALL_ALL, install_all, schema=_INSTALL_ALL_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_INSTALL_ASSET, install_asset, schema=_INSTALL_ASSET_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_CHECK_UPDATES, check_updates)


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            for service in (
                SERVICE_INSTALL_ALL,
                SERVICE_INSTALL_ASSET,
                SERVICE_CHECK_UPDATES,
            ):
                hass.services.async_remove(DOMAIN, service)
    return unloaded
