"""Unit tests for fr_env_resolver constants."""

import os
from fr_env_resolver.constants import (
    TOOL_KEYS,
    DEFAULT_ICON,
    CONFIG_KEY,
    ENV,
    REZ_FR_ENV_RESOLVER_VERSION,
    CORE_PACKAGES,
    DEFAULT_VARIANT,
)


class TestConstants:
    """Test cases for constants module."""

    def test_tool_keys(self):
        """Test TOOL_KEYS constant."""
        expected_keys = ("title", "command", "description", "icon", "category", "filters", "variants", "environ")
        assert TOOL_KEYS == expected_keys

    def test_default_icon(self):
        """Test DEFAULT_ICON constant."""
        assert DEFAULT_ICON == "TODO"

    def test_config_key(self):
        """Test CONFIG_KEY namespace."""
        assert CONFIG_KEY.TOOL == "env_tool"
        assert CONFIG_KEY.CONTEXT == "env_context"
        assert CONFIG_KEY.MANIFEST == "env_manifest"

    def test_env_variables(self):
        """Test ENV namespace."""
        assert ENV.TOOL_SEARCH_PATH == "FR_TOOL_SEARCH_PATH"
        assert ENV.MANIFEST_PATH == "FR_MANIFEST_PATH"
        assert ENV.CONFIG_SCHEMA_PATH == "FR_CONFIG_SCHEMA_PATH"
        assert ENV.REZ_PRODUCTION_PATHS == "FR_REZ_PRODUCTION_PATHS"
        assert ENV.REZ_STAGING_PATHS == "FR_REZ_STAGING_PATHS"
        assert ENV.REZ_DEV_PATHS == "FR_REZ_DEV_PATHS"

    def test_default_variant(self):
        """Test DEFAULT_VARIANT constant."""
        assert DEFAULT_VARIANT == "default"

    def test_core_packages_from_env(self):
        """Test CORE_PACKAGES reads from environment variable."""
        # Test with empty environment variable
        if "FR_REZ_ENV_RESOLVER_CORE_PACKAGES" in os.environ:
            del os.environ["FR_REZ_ENV_RESOLVER_CORE_PACKAGES"]

        # Re-import to get fresh value
        from importlib import reload
        import fr_env_resolver.constants as constants_module

        reload(constants_module)

        assert constants_module.CORE_PACKAGES == ()

    def test_rez_version_from_env(self):
        """Test REZ_FR_ENV_RESOLVER_VERSION reads from environment."""
        # The actual value depends on the environment
        assert isinstance(REZ_FR_ENV_RESOLVER_VERSION, str)
