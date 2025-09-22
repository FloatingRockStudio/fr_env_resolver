"""Unit tests for fr_env_resolver core resolve functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from fr_env_resolver._internal.core.resolve import resolve_tool, resolve_tool_data, dict_to_dataclass, find_tools
from fr_env_resolver.structs import Tool, Environ


class TestResolveTool:
    """Test cases for resolve_tool function."""

    def test_resolve_tool_basic(self):
        """Test basic tool resolution."""
        data = {
            "environ": {"packages": ["test-package"]},
            "filters": [["os", "is", "windows"]],
        }

        result = resolve_tool(data)

        assert result.environ.packages == ["test-package"]
        assert result.filters == [["os", "is", "windows"]]

    def test_resolve_tool_with_descriptor(self):
        """Test tool resolution with descriptor."""
        descriptor = Tool(
            name="test_tool",
            command="test.exe",
            icon="test.png",
            category="Test",
            title="Test Tool",
            description="Test Description",
            path=Path("/test/path"),
        )

        data = {
            "environ": {"packages": ["test-package"]},
            "filters": [["os", "is", "windows"]],
        }

        result = resolve_tool(data, descriptor=descriptor)

        assert result.name == "test_tool"
        assert result.command == "test.exe"
        assert result.icon == "test.png"
        assert result.category == "Test"
        assert result.title == "Test Tool"
        assert result.description == "Test Description"
        assert result.environ.packages == ["test-package"]
        assert result.filters == [["os", "is", "windows"]]

    def test_resolve_tool_with_variants(self):
        """Test tool resolution with variants."""
        descriptor = Tool(
            name="test_tool",
            command="test.exe",
            icon="test.png",
            category="Test",
            title="Test Tool",
            description="Test Description",
            path=Path("/test/path"),
            variants={"base_variant": Tool(name="base", command="base.exe")},
        )

        data = {"variants": {"test_variant": {"command": "test_variant.exe", "title": "Test Variant"}}}

        result = resolve_tool(data, descriptor=descriptor)

        assert result.name == "test_tool"
        assert "base_variant" in result.variants
        assert result.variants["base_variant"].command == "base.exe"

    def test_resolve_tool_merges_filters(self):
        """Test that tool resolution properly merges filters."""
        data = {"filters": [["installed_apps", "contains", "Test App"]]}

        result = resolve_tool(data)

        assert result.filters == [["installed_apps", "contains", "Test App"]]

    def test_resolve_tool_with_environ_workflow(self):
        """Test tool resolution with workflow in environ."""
        data = {"environ": {"workflow": "test_workflow", "packages": ["test-package"], "override": True}}

        result = resolve_tool(data)

        assert result.environ.workflow == "test_workflow"
        assert result.environ.packages == ["test-package"]
        assert result.environ.override is True

    def test_resolve_tool_icon_path_resolution(self):
        """Test that icon paths are resolved relative to tool path."""
        tool_path = Path("/tools/collection.frtool")
        descriptor = Tool(name="test_tool", icon="./icons/test.png", path=tool_path)
        data = {"icon": "./icons/test.png"}

        result = resolve_tool(data, descriptor=descriptor)

        # Icon should be resolved relative to the tool's path
        # Just check that it ends with the expected path components
        assert result.icon.endswith("tools/icons/test.png") or result.icon.endswith("tools\\icons\\test.png")

    def test_resolve_tool_preserves_descriptor_values(self):
        """Test that descriptor values are preserved when data is empty."""
        descriptor = Tool(
            name="test_tool",
            command="test.exe",
            icon="test.png",
            category="Test",
            title="Test Tool",
            description="Test Description",
            filters=[["os", "is", "windows"]],
            environ=Environ(packages=["desc-package"], workflow="desc-workflow"),
            path=Path("/test/path"),
        )

        data = {}  # Empty data

        result = resolve_tool(data, descriptor=descriptor)

        # All descriptor values should be preserved
        assert result.name == "test_tool"
        assert result.command == "test.exe"
        assert result.icon == "test.png"
        assert result.category == "Test"
        assert result.title == "Test Tool"
        assert result.description == "Test Description"
        assert result.filters == [["os", "is", "windows"]]
        assert result.environ.packages == ["desc-package"]
        assert result.environ.workflow == "desc-workflow"


class TestResolveToolData:
    """Test cases for resolve_tool_data function."""

    def test_resolve_tool_data_basic(self):
        """Test basic tool data resolution."""
        data = {
            "command": "test.exe",
            "category": "Test",
            "title": "Test Tool",
            "description": "Test Description",
        }
        path = Path("/tools/test.frtool")

        result = resolve_tool_data("test_tool", data, path)

        assert result.name == "test_tool"
        assert result.command == "test.exe"
        assert result.category == "Test"
        assert result.title == "Test Tool"
        assert result.description == "Test Description"
        assert result.path == path


class TestDictToDataclass:
    """Test cases for dict_to_dataclass function."""

    def test_dict_to_dataclass_tool(self):
        """Test converting dict to Tool dataclass."""
        data = {
            "name": "test_tool",
            "command": "test.exe",
            "category": "Test",
        }

        result = dict_to_dataclass(data, Tool)

        assert isinstance(result, Tool)
        assert result.name == "test_tool"
        assert result.command == "test.exe"
        assert result.category == "Test"

    def test_dict_to_dataclass_environ(self):
        """Test converting dict to Environ dataclass."""
        data = {
            "packages": ["test-package"],
            "workflow": "test_workflow",
            "override": True,
        }

        result = dict_to_dataclass(data, Environ)

        assert isinstance(result, Environ)
        assert result.packages == ["test-package"]
        assert result.workflow == "test_workflow"
        assert result.override is True


class TestFindTools:
    """Test cases for find_tools function."""

    def test_find_tools_empty_paths(self):
        """Test find_tools with empty path string."""
        with patch.dict("os.environ", {}, clear=True):
            result = list(find_tools(""))
            assert result == []

    def test_find_tools_nonexistent_paths(self):
        """Test find_tools with nonexistent paths."""
        result = list(find_tools("/nonexistent/path"))
        assert result == []
