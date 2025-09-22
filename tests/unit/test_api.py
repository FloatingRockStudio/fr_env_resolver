"""Unit tests for fr_env_resolver main API classes."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path

from fr_env_resolver import EnvResolver, ToolUpdater, EnvUpdater, ManifestUpdater
from fr_env_resolver.structs import Tool, Environ


class TestEnvResolverInit:
    """Test cases for EnvResolver initialization."""

    @patch("fr_env_resolver._internal.impl.resolver.ConfigLoader")
    def test_env_resolver_creation_with_string_path(self, mock_config_loader):
        """Test creating EnvResolver with string path."""
        mock_config_loader.return_value = Mock()

        resolver = EnvResolver("/test/path")

        # Should convert string to Path
        mock_config_loader.assert_called()

    @patch("fr_env_resolver._internal.impl.resolver.ConfigLoader")
    def test_env_resolver_creation_with_path_object(self, mock_config_loader):
        """Test creating EnvResolver with Path object."""
        mock_config_loader.return_value = Mock()

        test_path = Path("/test/path")
        resolver = EnvResolver(test_path)

        mock_config_loader.assert_called()

    @patch("fr_env_resolver._internal.impl.resolver.ConfigLoader")
    def test_env_resolver_with_variant(self, mock_config_loader):
        """Test creating EnvResolver with variant."""
        mock_config_loader.return_value = Mock()

        resolver = EnvResolver("/test/path", variant="test_variant")

        # Verify ConfigLoader was called with variant
        mock_config_loader.assert_called()


class TestPublicAPIImports:
    """Test cases for public API imports."""

    def test_main_api_imports(self):
        """Test that main API classes can be imported."""
        # These should not raise import errors
        from fr_env_resolver import EnvResolver, ToolUpdater, EnvUpdater, ManifestUpdater

        assert EnvResolver is not None
        assert ToolUpdater is not None
        assert EnvUpdater is not None
        assert ManifestUpdater is not None

    def test_compatibility_imports(self):
        """Test that classes are available from the main module."""
        # These should not raise import errors - now they come from main module
        from fr_env_resolver import EnvResolver
        from fr_env_resolver import ToolUpdater
        from fr_env_resolver.exceptions import ValidationException

        assert EnvResolver is not None
        assert ToolUpdater is not None
        assert ValidationException is not None

    def test_structs_import(self):
        """Test that structs can be imported."""
        from fr_env_resolver.structs import Tool, Environ, ProductionInfo

        assert Tool is not None
        assert Environ is not None
        assert ProductionInfo is not None

    def test_constants_import(self):
        """Test that constants can be imported."""
        from fr_env_resolver.constants import CONFIG_KEY, ENV, TOOL_KEYS

        assert CONFIG_KEY is not None
        assert ENV is not None
        assert TOOL_KEYS is not None


class TestToolUpdaterPublicAPI:
    """Test cases for ToolUpdater public API."""

    def test_tool_updater_instantiation(self):
        """Test ToolUpdater can be instantiated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should not raise an exception
            updater = ToolUpdater(temp_dir, "test", load=False)
            assert hasattr(updater, "tools")
            assert hasattr(updater, "commit")

    def test_tool_updater_tools_property(self):
        """Test ToolUpdater tools property."""
        with tempfile.TemporaryDirectory() as temp_dir:
            updater = ToolUpdater(temp_dir, "test", load=False)

            # Should start with empty list
            assert updater.tools == []

            # Should be able to set tools
            tool = Tool(name="test")
            updater.tools = [tool]
            assert len(updater.tools) == 1
            assert updater.tools[0] == tool


class TestEnvUpdaterPublicAPI:
    """Test cases for EnvUpdater public API."""

    def test_env_updater_class_exists(self):
        """Test EnvUpdater class can be imported and has expected attributes."""
        # Test that class exists and has expected methods
        assert hasattr(EnvUpdater, "__init__")
        assert callable(getattr(EnvUpdater, "__init__"))


class TestManifestUpdaterPublicAPI:
    """Test cases for ManifestUpdater public API."""

    def test_manifest_updater_class_exists(self):
        """Test ManifestUpdater class can be imported and has expected attributes."""
        # Test that class exists and has expected methods
        assert hasattr(ManifestUpdater, "__init__")
        assert callable(getattr(ManifestUpdater, "__init__"))
