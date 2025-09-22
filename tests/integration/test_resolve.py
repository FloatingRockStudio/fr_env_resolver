import os
import pytest
from pathlib import Path

from fr_env_resolver import EnvResolver
from fr_env_resolver.structs import Tool, Environ
from fr_env_resolver.constants import CONFIG_KEY, ENV
from fr_env_resolver._internal.core.resolve import resolve_tool
from dataclasses import asdict

# Try to import fr_common but make it optional
try:
    from fr_common.structs import Context

    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False
    Context = None


def test_resolve_tool_maya(tool_configs_dir):
    """Test tool resolution with Maya example."""
    tool_path = tool_configs_dir
    # data is what comes out of the cascading resolve
    data = {
        "environ": {"packages": ["extra_package"]},
        "filters": [["$installed_apps", "contains_expr", "Autodesk Maya.*"]],
        "variants": {"test": {"command": "maya.exe -test"}},
    }
    descriptor = Tool(
        name="maya",
        environ=Environ(
            workflow="maya",
        ),
        category="3D",
        command="maya.exe",
        icon=(tool_path / "maya_icon.png").resolve().as_posix(),
        title="MAYA",
        description="Launch Maya",
        filters=[["os", "is", "windows"]],
        path=tool_path,
    )
    expected = Tool(
        name="maya",
        command="maya.exe",
        icon=(tool_path / "maya_icon.png").resolve().as_posix(),
        title="MAYA",
        category="3D",
        description="Launch Maya",
        filters=[["$installed_apps", "contains_expr", "Autodesk Maya.*"], ["os", "is", "windows"]],
        environ=Environ(workflow="maya", packages=["extra_package"]),
        path=tool_path,
        variants={
            "test": Tool(
                name="test",
                command="maya.exe -test",
                icon=(tool_path / "maya_icon.png").resolve().as_posix(),
                title="MAYA",
                category="3D",
                description="Launch Maya",
                filters=[["os", "is", "windows"], ["$installed_apps", "contains_expr", "Autodesk Maya.*"]],
                environ=Environ(workflow="maya", packages=["extra_package"]),
                variants={},
                path=tool_path,
            )
        },
    )
    tool = resolve_tool(data, descriptor=descriptor)
    assert tool == expected


def test_resolve_tools():
    tool_path = Path(os.getenv("FR_TOOL_SEARCH_PATH"))
    resolver = EnvResolver(Context.from_path("/FR_ENV/Shots/SEQ_001/0010").path())
    tools = resolver.tools()

    assert tools == [
        Tool(
            name="maya",
            command="maya.exe",
            category="3D",
            icon=(tool_path / "./maya_icon.png").resolve().as_posix(),
            title="MAYA",
            description="Launch Maya",
            filters=[["os", "is", "windows"]],
            environ=Environ(packages=["extra_package"], workflow="maya", variables={}, override=False),
            variants={},
            path=tool_path / "maya.frtool",
        ),
        Tool(
            name="slating_tool",
            command="slating_tool",
            category="Production",
            icon="X:/Pipeline/Prism2/LauncherIcons/frslatingtool.png",
            title="SLATE",
            description="SURV Slating tool",
            filters=[
                ["context.project", "is", "FR_ENV"],
                ["user.groups", "contains", "techartist"],
                ["user.groups", "contains", "developer"],
            ],
            environ=Environ(packages=["fr_slating_tool", "python-3.9.7"], workflow=None, variables={}, override=True),
            variants={
                "pro_mode": Tool(
                    name="pro_mode",
                    category="Production",
                    command="slating_tool --pro-mode",
                    icon="X:/Pipeline/Prism2/LauncherIcons/frslatingtool.png",
                    title="SLATE",
                    description="Allow skipping of validations",
                    filters=[
                        ["access_level", ">=", "${access.TECHNICAL}"],
                        ["context.project", "is", "FR_ENV"],
                        ["user.groups", "contains", "techartist"],
                        ["user.groups", "contains", "developer"],
                    ],
                    environ=Environ(
                        packages=["custom_pro_package-0.0.1", "fr_slating_tool", "python-3.9.7"],
                        workflow=None,
                        variables={},
                        override=True,
                    ),
                    path=tool_path / "slating.frtool",
                )
            },
            path=tool_path / "slating.frtool",
        ),
        Tool(
            name="slate_uploader",
            category="Production",
            command="slate_uploader",
            icon="X:/Pipeline/Prism2/LauncherIcons/frslatingtool_uploader.png",
            title="SLATE Upload",
            description="SURV Slating uploader",
            filters=[
                {"$and": [[["context.sequence", "in", ["SEQ_001", "SEQ_002"]]], [["context.project", "is", "FR_ENV"]]]}
            ],
            environ=Environ(packages=["fr_slating_tool", "python-3.9.7"], workflow=None, variables={}, override=True),
            variants={},
            path=tool_path / "slating.frtool",
        ),
    ]


def test_resolve_find_tool():
    tool_path = Path(os.getenv("FR_TOOL_SEARCH_PATH"))
    resolver = EnvResolver(Context.from_path("/FR_ENV/Shots/SEQ_001/0010").path())

    tool = resolver.find_tool("maya")
    assert tool == Tool(
        name="maya",
        category="3D",
        command="maya.exe",
        icon=(tool_path / "./maya_icon.png").resolve().as_posix(),
        title="MAYA",
        description="Launch Maya",
        filters=[["os", "is", "windows"]],
        environ=Environ(packages=["extra_package"], workflow="maya", variables={}, override=False),
        variants={},
        path=tool_path / "maya.frtool",
    )
    tool = resolver.find_tool("slating_tool")
    assert tool == Tool(
        name="slating_tool",
        category="Production",
        command="slating_tool",
        icon="X:/Pipeline/Prism2/LauncherIcons/frslatingtool.png",
        title="SLATE",
        description="SURV Slating tool",
        filters=[
            ["context.project", "is", "FR_ENV"],
            ["user.groups", "contains", "techartist"],
            ["user.groups", "contains", "developer"],
        ],
        environ=Environ(packages=["fr_slating_tool", "python-3.9.7"], workflow=None, variables={}, override=True),
        variants={
            "pro_mode": Tool(
                name="pro_mode",
                category="Production",
                command="slating_tool --pro-mode",
                icon="X:/Pipeline/Prism2/LauncherIcons/frslatingtool.png",
                title="SLATE",
                description="Allow skipping of validations",
                filters=[
                    ["access_level", ">=", "${access.TECHNICAL}"],
                    ["context.project", "is", "FR_ENV"],
                    ["user.groups", "contains", "techartist"],
                    ["user.groups", "contains", "developer"],
                ],
                environ=Environ(
                    packages=["custom_pro_package-0.0.1", "fr_slating_tool", "python-3.9.7"],
                    workflow=None,
                    variables={},
                    override=True,
                ),
                variants={},
                path=tool_path / "slating.frtool",
            )
        },
        path=tool_path / "slating.frtool",
    )

    tool = resolver.find_tool("slating_tool", variant="pro_mode")
    assert tool == Tool(
        name="pro_mode",
        category="Production",
        command="slating_tool --pro-mode",
        icon="X:/Pipeline/Prism2/LauncherIcons/frslatingtool.png",
        title="SLATE",
        description="Allow skipping of validations",
        filters=[
            ["access_level", ">=", "${access.TECHNICAL}"],
            ["context.project", "is", "FR_ENV"],
            ["user.groups", "contains", "techartist"],
            ["user.groups", "contains", "developer"],
        ],
        environ=Environ(
            packages=["custom_pro_package-0.0.1", "fr_slating_tool", "python-3.9.7"],
            workflow=None,
            variables={},
            override=True,
        ),
        variants={},
        path=tool_path / "slating.frtool",
    )


def test_resolve_environ():
    # base resolve
    tool_path = Path(os.getenv("FR_TOOL_SEARCH_PATH"))
    resolver = EnvResolver(Context.from_path("/FR_ENV/Shots/SEQ_001/0010").path())

    env = resolver.resolve_environment()
    assert env == Environ(
        packages=["PySide2-5.15.2", "python-3.10.2", "custom_package.0.0.1+"],
        variables={
            "ENABLE_LEGACY_RENDER": "1",
            "PATH": "/path/to/root/thing;/path/to/shot/specific/thing",
            "PREPATH": "/path/to/shot/other/thing;/path/to/other/thing",
        },
    )

    # resolve tool
    tool = resolver.find_tool("maya")
    env = resolver.resolve_environment(tool)
    assert env == Environ(
        packages=[
            "PySide2-5.15.2",
            "python-3.9.7",
            "custom_package.0.0.1+",
            "maya-2023.4",
            "pymel-4",
            "another_package.0.0.2+",
            "extra_package",
        ],
        variables={
            "ENABLE_LEGACY_RENDER": "1",
            "PATH": "/path/to/root/thing;/path/to/shot/specific/thing",
            "PREPATH": "/path/to/shot/other/thing;/path/to/other/thing",
            "MAYA_RENDER_SETUP_INCLUDE_ALL_LIGHTS": "1",
            "MAYA_SCRIPT_PATH": "/path/to/mel/scripts;/path/to/shot/mel/scripts",
        },
        workflow="maya",
    )
    # resolve override
    tool = resolver.find_tool("slating_tool")
    env = resolver.resolve_environment(tool)
    assert env == Environ(
        packages=["fr_slating_tool", "python-3.9.7"],
        variables={},
        override=True,
    )

    # resolve variant
    env = resolver.resolve_environment(tool.variants["pro_mode"])
    assert env == Environ(
        packages=["custom_pro_package-0.0.1", "fr_slating_tool", "python-3.9.7"],
        variables={},
        override=True,
    )


def test_resolve_shell_setup():
    resolver = EnvResolver(Context.from_path("/FR_ENV/Shots/SEQ_001/0010").path())
    tool = resolver.find_tool("maya")
    env = resolver.resolve_environment(tool)


def test_resolve_manifest():
    # base resolve
    tool_path = Path(os.getenv("FR_TOOL_SEARCH_PATH"))
    resolver = EnvResolver(Context.from_path("/FR_ENV/Shots/SEQ_001/0030").path())
    env = resolver.resolve_environment()
    assert env == Environ(
        packages=["PySide2-5.15.2", "python-3.10", "custom_package-0.0.1+"],
        variables={
            "ENABLE_LEGACY_RENDER": "0",
            "PATH": "/path/to/root/thing",
            "PREPATH": "/path/to/other/thing",
        },
        manifest="VP20",
    )

    # resolve maya
    tool = resolver.find_tool("maya")
    env = resolver.resolve_environment(tool)
    assert env == Environ(
        packages=[
            "PySide2-5.15.2",
            "python-3.9.7",
            "maya-2023.2",
            "pymel-4",
            "vp-20",
            "custom_package-0.0.1+",
            "another_package-0.0.2+",
        ],
        variables={
            "ENABLE_LEGACY_RENDER": "0",
            "PATH": "/path/to/root/thing",
            "PREPATH": "/path/to/other/thing",
            "MAYA_RENDER_SETUP_INCLUDE_ALL_LIGHTS": "0",
            "MAYA_SCRIPT_PATH": "/path/to/mel/scripts",
        },
        workflow="maya",
        manifest="VP20",
    )
    # resolve houdini
    tool = resolver.find_tool("houdini")
    env = resolver.resolve_environment(tool)
    assert env == Environ(
        packages=[
            "PySide2-5.15.2",
            "python-3.10",
            "houdini-20.2.480",
            "custom_package-0.0.1+",
            "another_package-0.0.2+",
        ],
        variables={
            "ENABLE_LEGACY_RENDER": "0",
            "PATH": "/path/to/root/thing",
            "PREPATH": "/path/to/other/thing",
        },
        workflow="houdini",
        manifest="VP22",
    )
