"""Unit tests for fr_env_resolver data structures."""

import pytest
from fr_env_resolver.structs import Environ, Tool, ProductionInfo


class TestEnviron:
    """Test cases for the Environ dataclass."""

    def test_default_environ(self):
        """Test default Environ initialization."""
        env = Environ()
        assert env.packages == []
        assert env.workflow is None
        assert env.manifest == ""
        assert env.variables == {}
        assert env.override is False

    def test_environ_with_values(self):
        """Test Environ with custom values."""
        env = Environ(
            packages=["maya-2023", "python-3.9"],
            workflow="maya",
            manifest="vfx2023",
            variables={"TEST_VAR": "test_value"},
            override=True,
        )
        assert env.packages == ["maya-2023", "python-3.9"]
        assert env.workflow == "maya"
        assert env.manifest == "vfx2023"
        assert env.variables == {"TEST_VAR": "test_value"}
        assert env.override is True

    def test_is_default(self):
        """Test is_default method."""
        default_env = Environ()
        assert default_env.is_default()

        custom_env = Environ(packages=["maya-2023"])
        assert not custom_env.is_default()

        custom_workflow = Environ(workflow="maya")
        assert not custom_workflow.is_default()

    def test_environ_equality(self):
        """Test Environ equality comparison."""
        env1 = Environ(packages=["maya-2023"], workflow="maya")
        env2 = Environ(packages=["maya-2023"], workflow="maya")
        env3 = Environ(packages=["houdini-19"], workflow="houdini")

        assert env1 == env2
        assert env1 != env3


class TestTool:
    """Test cases for the Tool dataclass."""

    def test_default_tool(self):
        """Test default Tool initialization."""
        tool = Tool()
        assert tool.name is None
        assert tool.category is None
        assert tool.command is None
        assert tool.icon is None
        assert tool.title is None
        assert tool.description is None
        assert tool.filters == []
        assert tool.environ == Environ()
        assert tool.variants == {}
        assert tool.path is None

    def test_tool_with_values(self):
        """Test Tool with custom values."""
        environ = Environ(packages=["maya-2023"], workflow="maya")
        tool = Tool(
            name="maya",
            category="3D",
            command="maya.exe",
            icon="maya.png",
            title="Maya",
            description="3D Software",
            filters=[["os", "is", "windows"]],
            environ=environ,
            variants={"test": Tool(name="maya_test")},
        )

        assert tool.name == "maya"
        assert tool.category == "3D"
        assert tool.command == "maya.exe"
        assert tool.icon == "maya.png"
        assert tool.title == "Maya"
        assert tool.description == "3D Software"
        assert tool.filters == [["os", "is", "windows"]]
        assert tool.environ == environ
        assert "test" in tool.variants
        assert tool.variants["test"].name == "maya_test"

    def test_tool_with_default_environ(self):
        """Test that Tool has default Environ even when not specified."""
        tool = Tool(name="test")
        assert isinstance(tool.environ, Environ)
        assert tool.environ.is_default()


class TestProductionInfo:
    """Test cases for the ProductionInfo dataclass."""

    def test_production_info(self):
        """Test ProductionInfo initialization."""
        info = ProductionInfo(api_name="shotgun", url="https://studio.shotgunsoftware.com", project_code="TEST")

        assert info.api_name == "shotgun"
        assert info.url == "https://studio.shotgunsoftware.com"
        assert info.project_code == "TEST"

    def test_production_info_with_none_values(self):
        """Test ProductionInfo with None values."""
        info = ProductionInfo(api_name="ftrack", url=None, project_code=None)

        assert info.api_name == "ftrack"
        assert info.url is None
        assert info.project_code is None
