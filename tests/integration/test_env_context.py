import pytest
from pathlib import Path

# Try to import Config but make it optional
try:
    from fr_config import Config
    from fr_common.structs import Context

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    Config = None
    Context = None

from fr_env_resolver import EnvResolver


@pytest.mark.skipif(not CONFIG_AVAILABLE, reason="fr_config or fr_common not available")
def test_load_shot():
    """Test loading shot configuration - requires fr_config."""
    config = Config("env_context", Context.from_path("/FR_ENV/Shots/SEQ_001/0010").path())
    assert len(config.loaded_paths()) == 2
    assert config.path == Context.from_path("/FR_ENV/Shots/SEQ_001/0010").path()
    assert config.tags == ["published", "latest"]
    assert config.variants == ["default"]

    assert config._schema == {
        "__version__": 1,
        "packages": {
            "cascade": "append",
            "items": {"type": "string", "compare": {"type": "string", "default": "^(?:[!~]*)([_a-zA-Z0-9]+)-?.*?"}},
            "type": "array",
            "unique": True,
        },
        "production_info": {
            "type": "object",
            "cascade": "replace",
            "items": {
                "api_name": {
                    "default": "",
                    "type": "string",
                },
                "project_code": {
                    "default": "",
                    "type": "string",
                },
                "type": "object",
                "url": {
                    "default": "",
                    "type": "string",
                },
            },
        },
        "workflows": {
            "cascade": "update",
            "items": {
                "type": "object",
                "override": {"type": "bool", "default": False},
                "packages": {
                    "cascade": "append",
                    "items": {
                        "type": "string",
                        "compare": {"type": "string", "default": "^(?:[!~]*)([_a-zA-Z0-9]+)-?.*?"},
                    },
                    "type": "array",
                },
                "variables": {
                    "cascade": "update",
                    "items": {"type": "string", "separator": {"type": "string", "default": "%pathsep%"}},
                    "type": "object",
                },
                "manifest": {"type": "string", "default": ""},
            },
            "type": "object",
        },
        "variables": {
            "cascade": "update",
            "items": {"type": "string", "separator": {"type": "string", "default": "%pathsep%"}},
            "type": "object",
        },
        "manifest": {"type": "string", "default": ""},
    }

    assert config._data == {
        "variables": {
            "ENABLE_LEGACY_RENDER": "1",
            "PATH": "/path/to/root/thing;/path/to/shot/specific/thing",
            "PREPATH": "/path/to/shot/other/thing;/path/to/other/thing",
        },
        "production_info": {},
        "packages": ["PySide2-5.15.2", "python-3.10.2", "custom_package.0.0.1+"],
        "manifest": "",
        "workflows": {
            "maya": {
                "override": False,
                "packages": ["maya-2023.4", "pymel-4", "python-3.9.7", "another_package.0.0.2+"],
                "variables": {
                    "MAYA_RENDER_SETUP_INCLUDE_ALL_LIGHTS": "1",
                    "MAYA_SCRIPT_PATH": "/path/to/mel/scripts;/path/to/shot/mel/scripts",
                },
                "manifest": "",
            },
            "rv": {
                "override": False,
                "packages": ["rv_local_install", "rv_fr_plugins"],
                "variables": {"SOME_RV_FLAG": "0"},
                "manifest": "",
            },
        },
    }
    assert set(config.keys()) == {"variables", "packages", "production_info", "workflows", "manifest"}
    assert set(config.key_paths()) == {
        "/manifest",
        "/variables",
        "/variables/ENABLE_LEGACY_RENDER",
        "/variables/PATH",
        "/variables/PREPATH",
        "/packages",
        "/production_info",
        "/workflows",
        "/workflows/rv",
        "/workflows/rv/override",
        "/workflows/rv/manifest",
        "/workflows/rv/variables",
        "/workflows/rv/variables/SOME_RV_FLAG",
        "/workflows/rv/packages",
        "/workflows/maya",
        "/workflows/maya/override",
        "/workflows/maya/manifest",
        "/workflows/maya/variables",
        "/workflows/maya/variables/MAYA_RENDER_SETUP_INCLUDE_ALL_LIGHTS",
        "/workflows/maya/variables/MAYA_SCRIPT_PATH",
        "/workflows/maya/packages",
    }


def test_env_resolver_basic(shot_context_path):
    """Test basic environment resolver functionality."""
    resolver = EnvResolver(shot_context_path)

    # Test that we can get production info
    prod_info = resolver.production_info()
    assert prod_info is not None

    # Test that we can get tools
    tools = resolver.tools()
    assert isinstance(tools, list)

    # Test that we can resolve environment
    env = resolver.resolve_environment()
    assert env is not None
    assert hasattr(env, "packages")
    assert hasattr(env, "variables")


def test_env_resolver_tools(shot_context_path):
    """Test tool resolution."""
    resolver = EnvResolver(shot_context_path)
    tools = resolver.tools()

    if tools:
        # If tools exist, test find_tool functionality
        first_tool = tools[0]
        found_tool = resolver.find_tool(first_tool.name)
        assert found_tool is not None
        assert found_tool.name == first_tool.name

        # Test non-existent tool
        not_found = resolver.find_tool("non_existent_tool_12345")
        assert not_found is None


def test_env_resolver_workflow(shot_context_path):
    """Test workflow resolution."""
    resolver = EnvResolver(shot_context_path)

    # Test default environment
    default_env = resolver.resolve_environment()
    assert default_env is not None

    # Test with specific workflow
    maya_env = resolver.resolve_environment(workflow="maya")
    assert maya_env is not None

    # Environments might be different depending on configuration
    # We just verify they both resolve without error


def test_env_resolver_dump(shot_context_path):
    """Test dump functionality."""
    resolver = EnvResolver(shot_context_path)
    dump_output = resolver.dump()

    assert isinstance(dump_output, str)
    assert len(dump_output) > 0
    assert "Resolved Environment" in dump_output
