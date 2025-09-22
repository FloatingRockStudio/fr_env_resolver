"""Unit tests for fr_env_resolver validation logic."""

import pytest
from fr_env_resolver._internal.core.validate import validate_tool
from fr_env_resolver.structs import Tool, Environ
from fr_env_resolver.exceptions import ValidationException


class TestValidateTool:
    """Test cases for tool validation."""

    def test_validate_none_tool(self):
        """Test validation fails for None tool."""
        with pytest.raises(ValidationException, match="Tool cannot be None"):
            validate_tool(None)

    def test_validate_tool_without_name(self):
        """Test validation fails for tool without name."""
        tool = Tool()
        with pytest.raises(ValidationException, match="Tool name is required"):
            validate_tool(tool)

    def test_validate_tool_with_empty_name(self):
        """Test validation fails for tool with empty name."""
        tool = Tool(name="")
        with pytest.raises(ValidationException, match="Tool name is required"):
            validate_tool(tool)

    def test_validate_tool_with_whitespace_name(self):
        """Test validation fails for tool with whitespace in name."""
        tool = Tool(name="tool name")
        with pytest.raises(ValidationException, match="Tool name cannot contain whitespace"):
            validate_tool(tool)

    def test_validate_valid_tool_minimal(self):
        """Test validation passes for minimal valid tool."""
        tool = Tool(
            name="maya", command="maya.exe", icon="maya.png", category="3D", title="Maya", description="3D Software"
        )
        # Should not raise any exception
        validate_tool(tool)

    def test_validate_tool_missing_command(self):
        """Test validation fails for tool without command."""
        tool = Tool(name="maya", icon="maya.png", category="3D", title="Maya", description="3D Software")
        with pytest.raises(ValidationException, match="maya.command is empty"):
            validate_tool(tool)

    def test_validate_tool_missing_icon(self):
        """Test validation fails for tool without icon."""
        tool = Tool(name="maya", command="maya.exe", category="3D", title="Maya", description="3D Software")
        with pytest.raises(ValidationException, match="maya.icon is empty"):
            validate_tool(tool)

    def test_validate_tool_missing_category(self):
        """Test validation fails for tool without category."""
        tool = Tool(name="maya", command="maya.exe", icon="maya.png", title="Maya", description="3D Software")
        with pytest.raises(ValidationException, match="maya.category is empty"):
            validate_tool(tool)

    def test_validate_tool_missing_title(self):
        """Test validation fails for tool without title."""
        tool = Tool(name="maya", command="maya.exe", icon="maya.png", category="3D", description="3D Software")
        with pytest.raises(ValidationException, match="maya.title is empty"):
            validate_tool(tool)

    def test_validate_tool_missing_description(self):
        """Test validation fails for tool without description."""
        tool = Tool(name="maya", command="maya.exe", icon="maya.png", category="3D", title="Maya")
        with pytest.raises(ValidationException, match="maya.description is empty"):
            validate_tool(tool)

    def test_validate_tool_with_environ(self):
        """Test validation passes for tool with custom environ."""
        tool = Tool(
            name="maya",
            command="maya.exe",
            icon="maya.png",
            category="3D",
            title="Maya",
            description="3D Software",
            environ=Environ(packages=["maya-2023"], workflow="maya"),
        )
        # Should not raise any exception
        validate_tool(tool)

    def test_validate_tool_with_variants(self):
        """Test validation passes for tool with variants."""
        variant_tool = Tool(
            name="maya_test",
            command="maya.exe -test",
            icon="maya.png",
            category="3D",
            title="Maya Test",
            description="Maya Test Mode",
        )

        tool = Tool(
            name="maya",
            command="maya.exe",
            icon="maya.png",
            category="3D",
            title="Maya",
            description="3D Software",
            variants={"test": variant_tool},
        )
        # Should not raise any exception
        validate_tool(tool)
