"""Download Teds View Assist assets from GitHub and install them into HA/VA."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import shutil

from homeassistant.components.blueprint import importer
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    ASSET_BACKGROUNDS,
    ASSET_BLUEPRINTS,
    ASSET_DASHBOARD,
    ASSET_VIEWS,
    BLUEPRINT_SUBDIR,
    COMMUNITY_DIR,
    LOVELACE_STORAGE_FILE,
    SRC_BACKGROUNDS_DIR,
    SRC_DASHBOARD_DIR,
    SRC_SENTENCES_DIR,
    SRC_VIEWS_DIR,
    VA_BACKGROUNDS_PATH,
    VA_CONFIG_DIR,
    VA_DASHBOARD_DIR,
    VA_DOMAIN,
    VA_LOAD_ASSET_SERVICE,
    VA_VIEWS_DIR,
    VERSIONS_FILE,
)
from .github import GitHubClient, GitHubNotFound

_LOGGER = logging.getLogger(__name__)


class InstallerError(HomeAssistantError):
    """Raised when an asset cannot be installed."""


class Installer:
    """Stage repo assets on disk and register them with View Assist."""

    def __init__(self, hass: HomeAssistant, github: GitHubClient) -> None:
        """Initialise with a GitHub client for the configured repo."""
        self.hass = hass
        self.github = github

    async def async_get_repo_versions(self) -> dict:
        """Fetch and parse versions.json from the repo."""
        try:
            text = await self.github.async_get_text(VERSIONS_FILE)
        except GitHubNotFound as err:
            raise InstallerError(f"{VERSIONS_FILE} not found in the repository.") from err
        try:
            return json.loads(text)
        except ValueError as err:
            raise InstallerError(f"Invalid {VERSIONS_FILE}: {err}") from err

    async def async_install_all(self, versions: dict, force: bool = False) -> dict:
        """Install every asset whose repo version differs from ``versions``."""
        repo = await self.async_get_repo_versions()
        await self.async_snapshot_dashboard()
        new = self._copy_versions(versions)

        # Dashboard first — views rely on its button_card_templates.
        if force or new.get(ASSET_DASHBOARD) != repo.get(ASSET_DASHBOARD):
            await self._install_dashboard()
            new[ASSET_DASHBOARD] = repo.get(ASSET_DASHBOARD)

        repo_views = repo.get(ASSET_VIEWS, {})
        for name in await self._list_views():
            if force or new[ASSET_VIEWS].get(name) != repo_views.get(name):
                await self._install_view(name)
                new[ASSET_VIEWS][name] = repo_views.get(name)

        repo_bps = repo.get(ASSET_BLUEPRINTS, {})
        for group in await self._list_blueprint_groups():
            if force or new[ASSET_BLUEPRINTS].get(group) != repo_bps.get(group):
                await self._install_blueprint(group)
                new[ASSET_BLUEPRINTS][group] = repo_bps.get(group)

        if force or new.get(ASSET_BACKGROUNDS) != repo.get(ASSET_BACKGROUNDS):
            await self._install_backgrounds()
            new[ASSET_BACKGROUNDS] = repo.get(ASSET_BACKGROUNDS)

        return new

    async def async_install_asset(
        self, versions: dict, asset_class: str, name: str | None = None
    ) -> dict:
        """Install one asset class (optionally a single named view/blueprint)."""
        repo = await self.async_get_repo_versions()
        new = self._copy_versions(versions)

        if asset_class == ASSET_DASHBOARD:
            await self._install_dashboard()
            new[ASSET_DASHBOARD] = repo.get(ASSET_DASHBOARD)
        elif asset_class == ASSET_VIEWS:
            for item in [name] if name else await self._list_views():
                await self._install_view(item)
                new[ASSET_VIEWS][item] = repo.get(ASSET_VIEWS, {}).get(item)
        elif asset_class == ASSET_BLUEPRINTS:
            for item in [name] if name else await self._list_blueprint_groups():
                await self._install_blueprint(item)
                new[ASSET_BLUEPRINTS][item] = repo.get(ASSET_BLUEPRINTS, {}).get(item)
        elif asset_class == ASSET_BACKGROUNDS:
            await self._install_backgrounds()
            new[ASSET_BACKGROUNDS] = repo.get(ASSET_BACKGROUNDS)
        else:
            raise InstallerError(f"Unknown asset class: {asset_class}")

        return new

    # -- per-asset installs -------------------------------------------------

    async def _list_views(self) -> list[str]:
        entries = await self.github.async_list_dir(SRC_VIEWS_DIR)
        return [
            e["name"]
            for e in entries
            if e["type"] == "dir" and e["name"] != COMMUNITY_DIR
        ]

    async def _list_blueprint_groups(self) -> list[str]:
        try:
            entries = await self.github.async_list_dir(SRC_SENTENCES_DIR)
        except GitHubNotFound:
            return []
        return [
            e["name"]
            for e in entries
            if e["type"] == "dir" and e["name"] != COMMUNITY_DIR
        ]

    async def _install_dashboard(self) -> None:
        dest = Path(self.hass.config.path(VA_CONFIG_DIR, VA_DASHBOARD_DIR))
        await self.github.async_download_dir(SRC_DASHBOARD_DIR, dest)
        await self._call_load_asset(ASSET_DASHBOARD, "dashboard", backup=False)

    async def _install_view(self, name: str) -> None:
        dest = Path(self.hass.config.path(VA_CONFIG_DIR, VA_VIEWS_DIR, name))
        await self.github.async_download_dir(f"{SRC_VIEWS_DIR}/{name}", dest)
        await self._call_load_asset(ASSET_VIEWS, name, backup=True)

    async def _install_backgrounds(self) -> None:
        dest = Path(self.hass.config.path(*VA_BACKGROUNDS_PATH))
        await self.github.async_download_dir(SRC_BACKGROUNDS_DIR, dest)

    async def _install_blueprint(self, group: str) -> None:
        entries = await self.github.async_list_dir(f"{SRC_SENTENCES_DIR}/{group}")
        bp_file = next(
            (
                e
                for e in entries
                if e["type"] == "file"
                and e["name"].startswith("blueprint-")
                and e["name"].endswith(".yaml")
            ),
            None,
        )
        if bp_file is None:
            _LOGGER.warning("No blueprint-*.yaml found in %s/%s", SRC_SENTENCES_DIR, group)
            return
        imported = await importer.fetch_blueprint_from_github_url(
            self.hass, self.github.raw_url(bp_file["path"])
        )
        domain_blueprints = self.hass.data.get("blueprint", {}).get(imported.blueprint.domain)
        if domain_blueprints is None:
            raise InstallerError(
                f"Blueprint domain '{imported.blueprint.domain}' is not loaded."
            )
        await domain_blueprints.async_add_blueprint(
            imported.blueprint, f"{BLUEPRINT_SUBDIR}/{bp_file['name']}", allow_override=True
        )

    async def _call_load_asset(self, asset_class: str, name: str, backup: bool) -> None:
        if not self.hass.services.has_service(VA_DOMAIN, VA_LOAD_ASSET_SERVICE):
            raise InstallerError(
                "View Assist is not ready (view_assist.load_asset is unavailable). "
                "Install and configure View Assist first."
            )
        await self.hass.services.async_call(
            VA_DOMAIN,
            VA_LOAD_ASSET_SERVICE,
            {
                "asset_class": asset_class,
                "name": name,
                "download_from_repo": False,
                "backup_current_asset": backup,
            },
            blocking=True,
        )

    # -- backup / helpers ---------------------------------------------------

    async def async_snapshot_dashboard(self) -> None:
        """Copy the VA storage dashboard to a one-time backup if not already done."""
        src = Path(self.hass.config.path(LOVELACE_STORAGE_FILE))
        dst = Path(self.hass.config.path(f"{LOVELACE_STORAGE_FILE}.teds-backup"))
        await self.hass.async_add_executor_job(self._snapshot, src, dst)

    @staticmethod
    def _snapshot(src: Path, dst: Path) -> None:
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    @staticmethod
    def _copy_versions(versions: dict) -> dict:
        return {
            ASSET_DASHBOARD: versions.get(ASSET_DASHBOARD),
            ASSET_VIEWS: dict(versions.get(ASSET_VIEWS, {})),
            ASSET_BLUEPRINTS: dict(versions.get(ASSET_BLUEPRINTS, {})),
            ASSET_BACKGROUNDS: versions.get(ASSET_BACKGROUNDS),
        }
