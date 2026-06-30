"""Minimal GitHub content client for Ted's View Assist Installer.

Directory listings use the REST contents API (rate-limited; a HACS token, if
present, lifts the limit). File contents come from raw.githubusercontent.com.
"""

from __future__ import annotations

import logging
from pathlib import Path
import urllib.parse

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

MAX_DIR_DEPTH = 6


class GitHubError(Exception):
    """Generic GitHub access error."""


class GitHubRateLimit(GitHubError):
    """GitHub API rate limit exceeded."""


class GitHubNotFound(GitHubError):
    """Requested path was not found."""


class GitHubClient:
    """Download files and directories from a public GitHub repo."""

    def __init__(self, hass: HomeAssistant, repo: str, branch: str) -> None:
        """Initialise for a given owner/repo and branch."""
        self.hass = hass
        self.repo = repo.strip().strip("/")
        self.branch = branch.strip()
        self._api = f"https://api.github.com/repos/{self.repo}"
        self._raw = f"https://raw.githubusercontent.com/{self.repo}/{self.branch}"

    def _token(self) -> str | None:
        """Reuse a HACS personal access token, if available, to lift rate limits."""
        if hacs := self.hass.data.get("hacs"):
            try:
                return hacs.configuration.token
            except AttributeError:
                return None
        return None

    async def _get_json(self, url: str):
        session = async_get_clientsession(self.hass)
        headers = {"Accept": "application/vnd.github+json"}
        if token := await self.hass.async_add_executor_job(self._token):
            headers["Authorization"] = f"Bearer {token}"
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            if resp.status == 403:
                raise GitHubRateLimit(
                    "GitHub API rate limit exceeded. Add a personal access "
                    "token to HACS to raise the limit."
                )
            if resp.status == 404:
                raise GitHubNotFound(f"Not found: {url}")
            raise GitHubError(f"GitHub API error {resp.status} for {url}")

    async def async_list_dir(self, path: str) -> list[dict]:
        """List the entries of a repo directory (single level)."""
        quoted = urllib.parse.quote(path)
        data = await self._get_json(f"{self._api}/contents/{quoted}?ref={self.branch}")
        if not isinstance(data, list):
            raise GitHubError(f"Path is not a directory: {path}")
        return data

    async def async_dir_exists(self, path: str) -> bool:
        """Return whether a repo directory exists."""
        try:
            await self.async_list_dir(path)
        except GitHubNotFound:
            return False
        return True

    async def async_get_bytes(self, path: str) -> bytes:
        """Download a single file's raw bytes."""
        session = async_get_clientsession(self.hass)
        quoted = urllib.parse.quote(path)
        async with session.get(f"{self._raw}/{quoted}") as resp:
            if resp.status == 200:
                return await resp.read()
            if resp.status == 404:
                raise GitHubNotFound(f"Not found: {path}")
            raise GitHubError(f"GitHub raw error {resp.status} for {path}")

    async def async_get_text(self, path: str) -> str:
        """Download a single file as UTF-8 text."""
        return (await self.async_get_bytes(path)).decode("utf-8")

    async def async_download_dir(self, repo_path: str, dest: Path, depth: int = 1) -> int:
        """Recursively download a repo directory into ``dest``; return file count."""
        count = 0
        for entry in await self.async_list_dir(repo_path):
            name = entry["name"]
            if entry["type"] == "dir":
                if depth >= MAX_DIR_DEPTH:
                    continue
                count += await self.async_download_dir(
                    entry["path"], dest / name, depth + 1
                )
            elif entry["type"] == "file":
                data = await self.async_get_bytes(entry["path"])
                await self.hass.async_add_executor_job(self._write_file, dest / name, data)
                count += 1
        return count

    def raw_url(self, path: str) -> str:
        """Return the raw.githubusercontent.com URL for a repo path."""
        return f"{self._raw}/{urllib.parse.quote(path)}"

    async def async_latest_release(self) -> tuple[str, str] | None:
        """Return ``(tag, body)`` of the latest published release, or ``None``."""
        try:
            data = await self._get_json(f"{self._api}/releases/latest")
        except GitHubNotFound:
            return None
        tag = data.get("tag_name")
        if not tag:
            return None
        return tag, data.get("body") or ""

    @staticmethod
    def _write_file(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
