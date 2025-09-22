# Copyright (C) 2024 Floating Rock Studio Ltd
"""Constants for fr_env_resolver package."""

from types import SimpleNamespace as _SimpleNamespace
import os as _os
from pathlib import Path as _Path

# Tool configuration keys
TOOL_KEYS = ("title", "command", "description", "icon", "category", "filters", "variants", "environ")
DEFAULT_ICON = "TODO"

# Configuration keys for different types
CONFIG_KEY = _SimpleNamespace(TOOL="env_tool", CONTEXT="env_context", MANIFEST="env_manifest")

# Environment variable names
ENV = _SimpleNamespace(
    TOOL_SEARCH_PATH="FR_TOOL_SEARCH_PATH",
    MANIFEST_PATH="FR_MANIFEST_PATH",
    CONFIG_SCHEMA_PATH="FR_CONFIG_SCHEMA_PATH",
    REZ_PRODUCTION_PATHS="FR_REZ_PRODUCTION_PATHS",
    REZ_STAGING_PATHS="FR_REZ_STAGING_PATHS",
    REZ_DEV_PATHS="FR_REZ_DEV_PATHS",
)

# Version information (replaces FR_ENV_RESOLVER_VERSION)
REZ_FR_ENV_RESOLVER_VERSION = _os.getenv("REZ_FR_ENV_RESOLVER_VERSION", "unknown")

# These packages will be loaded irrespective of tool configs in order to make the resolver work when not immediately launching
_core_packages_str = _os.getenv("FR_REZ_ENV_RESOLVER_CORE_PACKAGES", "")
CORE_PACKAGES = tuple(pkg for pkg in _core_packages_str.split(_os.pathsep) if pkg.strip())
# Default variant name
DEFAULT_VARIANT = "default"

SCHEMA_PATH = str(_Path(__file__).parent / "../schema")

# Append to schema search path, ideally this would not happen here but pip can't set env vars on install
# TODO: revisit this
if SCHEMA_PATH not in _os.getenv(ENV.CONFIG_SCHEMA_PATH, ""):
    _os.environ[ENV.CONFIG_SCHEMA_PATH] = (
        SCHEMA_PATH + _os.pathsep + _os.getenv(ENV.CONFIG_SCHEMA_PATH, "")
        if _os.getenv(ENV.CONFIG_SCHEMA_PATH, "")
        else SCHEMA_PATH
    )
