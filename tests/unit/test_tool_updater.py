"""Unit tests for fr_env_resolver tool updater functionality."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from fr_env_resolver._internal.impl.tool_updater import ToolUpdater, _tool_to_dict
from fr_env_resolver.structs import Tool, Environ
from fr_env_resolver.exceptions import ValidationException


class TestToolToDict:
    """Test cases for _tool_to_dict function."""

    def test_tool_to_dict_minimal(self):
        """Test conversion of minimal tool to dict."""
        tool = Tool(
            name="test",
            command="test.exe",
            icon="test.png",
            category="Test",
            title="Test Tool",
            description="Test Description",
        )

        result = _tool_to_dict(tool)

        expected = {
            "command": "test.exe",
            "icon": "test.png",
            "category": "Test",
            "title": "Test Tool",
            "description": "Test Description",
        }
        assert result == expected

    def test_tool_to_dict_with_environ(self):
        """Test conversion of tool with environ to dict."""
        environ = Environ(packages=["test-pkg"], workflow="test")
        tool = Tool(
            name="test",
            command="test.exe",
            icon="test.png",
            category="Test",
            title="Test Tool",
            description="Test Description",
            environ=environ,
        )

        result = _tool_to_dict(tool)

        assert "environ" in result
        assert result["environ"]["packages"] == ["test-pkg"]
        assert result["environ"]["workflow"] == "test"

    def test_tool_to_dict_default_environ_excluded(self):
        """Test that default environ is not included in dict."""
        tool = Tool(
            name="test",
            command="test.exe",
            icon="test.png",
            category="Test",
            title="Test Tool",
            description="Test Description",
            environ=Environ(),  # Default environ
        )

        result = _tool_to_dict(tool)

        assert "environ" not in result

    def test_tool_to_dict_with_variants(self):
        """Test conversion of tool with variants to dict."""
        variant = Tool(
            name="test_variant",
            command="test_variant.exe",
            icon="test.png",
            category="Test",
            title="Test Variant",
            description="Test Variant Description",
        )

        tool = Tool(
            name="test",
            command="test.exe",
            icon="test.png",
            category="Test",
            title="Test Tool",
            description="Test Description",
            variants={"variant": variant},
        )

        result = _tool_to_dict(tool)

        assert "variants" in result
        assert "variant" in result["variants"]
        assert result["variants"]["variant"]["command"] == "test_variant.exe"

    def test_tool_to_dict_excludes_none_values(self):
        """Test that None values are excluded from dict."""
        tool = Tool(
            name="test",
            command="test.exe",
            icon="test.png",
            category="Test",
            title="Test Tool",
            description="Test Description",
            # Leave other fields as None
        )

        result = _tool_to_dict(tool)

        # Should only contain non-None values
        expected_keys = {"command", "icon", "category", "title", "description"}
        assert set(result.keys()) == expected_keys


class TestToolUpdater:
    """Test cases for ToolUpdater class."""

    def test_tool_updater_creation(self):
        """Test creating ToolUpdater instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            updater = ToolUpdater(temp_dir, "test_collection", load=False)

            assert updater.tools == []
            assert updater._collection == "test_collection"
            assert updater._tool_dir == Path(temp_dir)

    def test_tool_updater_invalid_collection_name(self):
        """Test ToolUpdater raises error for invalid collection name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValidationException, match="Collection name is invalid"):
                ToolUpdater(temp_dir, "123invalid", load=False)  # starts with number

    def test_tool_updater_valid_collection_names(self):
        """Test ToolUpdater accepts valid collection names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # These should not raise exceptions
            ToolUpdater(temp_dir, "test", load=False)
            ToolUpdater(temp_dir, "test123", load=False)
            ToolUpdater(temp_dir, "test_collection", load=False)

    @patch("fr_env_resolver._internal.impl.tool_updater.datetime")
    @patch("fr_env_resolver._internal.impl.tool_updater.os.getlogin")
    def test_tool_updater_commit(self, mock_getlogin, mock_datetime):
        """Test committing tools to file."""
        mock_getlogin.return_value = "testuser"
        mock_datetime.datetime.now.return_value.strftime.return_value = "01/01/2024, 12:00:00"

        with tempfile.TemporaryDirectory() as temp_dir:
            updater = ToolUpdater(temp_dir, "test", load=False)

            tool = Tool(
                name="test_tool",
                command="test.exe",
                icon="test.png",
                category="Test",
                title="Test Tool",
                description="Test Description",
            )
            updater.tools = [tool]

            result_path = updater.commit("Test commit")

            assert result_path.exists()
            assert result_path.name == "test.frtool"

            # Check file content
            with result_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            assert "__info__" in data
            assert data["__info__"]["author"] == "testuser"
            assert data["__info__"]["commit_message"] == "Test commit"
            assert "test_tool" in data
            assert data["test_tool"]["command"] == "test.exe"

    def test_tool_updater_commit_with_invalid_tool(self):
        """Test commit fails with invalid tool."""
        with tempfile.TemporaryDirectory() as temp_dir:
            updater = ToolUpdater(temp_dir, "test", load=False)

            # Add invalid tool (missing required fields)
            invalid_tool = Tool(name="invalid")
            updater.tools = [invalid_tool]

            with pytest.raises(ValidationException):
                updater.commit("Test commit")

    def test_tool_updater_validates_all_tools(self):
        """Test that all tools are validated before commit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            updater = ToolUpdater(temp_dir, "test", load=False)

            valid_tool = Tool(
                name="valid",
                command="valid.exe",
                icon="valid.png",
                category="Test",
                title="Valid Tool",
                description="Valid Description",
            )

            invalid_tool = Tool(name="invalid")  # Missing required fields

            updater.tools = [valid_tool, invalid_tool]

            with pytest.raises(ValidationException):
                updater.commit("Test commit")
