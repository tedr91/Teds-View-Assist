"""Constants for Ted's View Assist Installer."""

from __future__ import annotations

DOMAIN = "teds_view_assist_installer"

# Config entry options
CONF_REPO = "repo"
CONF_BRANCH = "branch"
DEFAULT_REPO = "tedr91/Teds-View-Assist"
DEFAULT_BRANCH = "main"

# Persistent store (.storage/teds_view_assist_installer)
STORAGE_VERSION = 1
STORAGE_KEY = DOMAIN

# How often to poll GitHub for a newer release.
UPDATE_CHECK_INTERVAL_HOURS = 6

# View Assist integration we delegate installs to.
VA_DOMAIN = "view_assist"
VA_LOAD_ASSET_SERVICE = "load_asset"

# Asset classes (keys used in versions.json + our store).
ASSET_DASHBOARD = "dashboard"
ASSET_VIEWS = "views"
ASSET_BLUEPRINTS = "blueprints"
ASSET_BACKGROUNDS = "backgrounds"
ASSET_CLASSES = (ASSET_DASHBOARD, ASSET_VIEWS, ASSET_BLUEPRINTS, ASSET_BACKGROUNDS)

# Source paths inside the GitHub repo.
SRC_DASHBOARD_DIR = "dashboard"
SRC_VIEWS_DIR = "views"
SRC_SENTENCES_DIR = "custom_sentences"
SRC_BACKGROUNDS_DIR = "backgrounds"
VERSIONS_FILE = "versions.json"
# Subfolder in views/ and custom_sentences/ that is not itself an installable asset.
COMMUNITY_DIR = "community_contributions"

# On-disk targets (relative to the HA config dir).
VA_CONFIG_DIR = "view_assist"
VA_VIEWS_DIR = "views"
VA_DASHBOARD_DIR = "dashboard"
# config/view_assist/images/backgrounds (VA's default rotate-background path).
VA_BACKGROUNDS_PATH = ("view_assist", "images", "backgrounds")
# Snapshot of the VA storage dashboard taken once before the first bulk install.
LOVELACE_STORAGE_FILE = ".storage/lovelace.view-assist"

# Blueprints we install go under config/blueprints/<domain>/teds_view_assist/.
BLUEPRINT_SUBDIR = "teds_view_assist"

# Services.
SERVICE_INSTALL_ALL = "install_all"
SERVICE_INSTALL_ASSET = "install_asset"
SERVICE_CHECK_UPDATES = "check_updates"
ATTR_ASSET_CLASS = "asset_class"
ATTR_NAME = "name"
ATTR_FORCE = "force"

# Store keys.
STORE_INSTALLED_TAG = "installed_tag"
STORE_VERSIONS = "versions"
