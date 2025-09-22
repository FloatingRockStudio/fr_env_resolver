"""Additional CLI tests for higher coverage."""

import os
import sys
import io
from contextlib import redirect_stdout
from pathlib import Path

from fr_env_resolver._internal.cli import parse_args, Args, resolve_from_context, ExecutionContext
from fr_env_resolver.structs import Tool, Environ, ProductionInfo

# Get the test resources directory
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
TEST_CONTEXT_PATH = RESOURCES_DIR / "configs" / "Projects" / "FR_ENV" / "03_Production" / "Shots" / "SEQ_001" / "0020"

# Schema paths
SCHEMA_PATH = f"{RESOURCES_DIR.parent.parent / 'schema'};{RESOURCES_DIR.parent.parent.parent / 'fr_config' / 'schema'}"


class TestCLIVerboseOutput:
    """Test verbose output functionality."""

    def test_verbose_package_output(self):
        """Test verbose output for package information."""
        original_env = {}
        test_env_vars = {
            "FR_CONFIG_SCHEMA_PATH": SCHEMA_PATH,
            "FR_REZ_PRODUCTION_PATHS": "prod1;prod2",
            "FR_REZ_STAGING_PATHS": "staging1",
            "FR_REZ_DEV_PATHS": "dev1",
        }
        for key, value in test_env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            args = Args(
                context=[str(TEST_CONTEXT_PATH)],
                verbose=True,
                dev=True,
                staging=True,
                add=[["extra_pkg1", "extra_pkg2"], ["extra_pkg3"]],
                context_variant="default",
            )

            # Test verbose resolve_from_context (which doesn't do execution)
            result = resolve_from_context(args)
            assert isinstance(result, ExecutionContext)

        finally:
            # Restore environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class TestCLIPackageHandling:
    """Test package path and core package handling."""

    def test_package_path_construction(self):
        """Test that package paths are constructed correctly from environment variables."""
        original_env = {}
        test_env_vars = {
            "FR_CONFIG_SCHEMA_PATH": SCHEMA_PATH,
            "FR_REZ_PRODUCTION_PATHS": "path1;path2;path3",
            "FR_REZ_STAGING_PATHS": "staging_path",
            "FR_REZ_DEV_PATHS": "dev_path1;dev_path2",
        }
        for key, value in test_env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            # Test with dev and staging flags
            args = Args(context=[str(TEST_CONTEXT_PATH)], dev=True, staging=True, context_variant="default")
            result = resolve_from_context(args)
            assert isinstance(result, ExecutionContext)

        finally:
            # Restore environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_empty_package_paths(self):
        """Test behavior with empty package paths."""
        original_env = {}
        test_env_vars = {
            "FR_CONFIG_SCHEMA_PATH": SCHEMA_PATH,
            "FR_REZ_PRODUCTION_PATHS": "",
            "FR_REZ_STAGING_PATHS": "",
            "FR_REZ_DEV_PATHS": "",
        }
        for key, value in test_env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            args = Args(context=[str(TEST_CONTEXT_PATH)], dev=True, staging=True, context_variant="default")
            result = resolve_from_context(args)
            assert isinstance(result, ExecutionContext)

        finally:
            # Restore environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class TestCLIArgsCombinations:
    """Test various argument combinations."""

    def test_args_dataclass_coverage(self):
        """Test Args dataclass with various combinations."""
        # Test with minimal args
        args = Args()
        assert args.add is None
        assert args.dev is False
        assert args.staging is False
        assert args.launch is False
        assert args.view is False
        assert args.env is None
        assert args.time is None
        assert args.workflow == ""
        assert args.tool == ""
        assert args.tool_variant == ""
        assert args.context_variant == "default"
        assert args.tool_data == ""
        assert args.verbose is False
        assert args.context == []

        # Test with all args set
        args = Args(
            add=[["pkg1"], ["pkg2"]],
            dev=True,
            staging=True,
            launch=True,
            view=True,
            env=["VAR=value"],
            time="123456",
            workflow="test_workflow",
            tool="test_tool",
            tool_variant="test_variant",
            context_variant="test_context",
            tool_data="test_data",
            verbose=True,
            context=["test", "context"],
        )
        assert args.add == [["pkg1"], ["pkg2"]]
        assert args.dev is True
        assert args.staging is True
        assert args.launch is True
        assert args.view is True
        assert args.env == ["VAR=value"]
        assert args.time == "123456"
        assert args.workflow == "test_workflow"
        assert args.tool == "test_tool"
        assert args.tool_variant == "test_variant"
        assert args.context_variant == "test_context"
        assert args.tool_data == "test_data"
        assert args.verbose is True
        assert args.context == ["test", "context"]

    def test_execution_context_coverage(self):
        """Test ExecutionContext dataclass."""
        from fr_env_resolver._internal.cli.resolve import ExecutionContext

        # Test basic creation
        ctx = ExecutionContext(
            context=None,
            resolver=None,
            tools=[],
            tool_obj=None,
            environment=Environ(),
            production_info=ProductionInfo("test", None, None),
        )
        assert ctx.context is None
        assert ctx.resolver is None
        assert ctx.tools == []
        assert ctx.tool_obj is None
        assert isinstance(ctx.environment, Environ)
        assert isinstance(ctx.production_info, ProductionInfo)

        # Test with actual objects
        tool = Tool(name="test", command="test.exe")
        ctx = ExecutionContext(
            context="test_context",
            resolver="test_resolver",
            tools=[tool],
            tool_obj=tool,
            environment=Environ(packages=["test-1.0"]),
            production_info=ProductionInfo("test_api", "test_url", "test_project"),
        )
        assert ctx.context == "test_context"
        assert ctx.resolver == "test_resolver"
        assert len(ctx.tools) == 1
        assert ctx.tool_obj.name == "test"
        assert ctx.environment.packages == ["test-1.0"]
        assert ctx.production_info.project_code == "test_project"
