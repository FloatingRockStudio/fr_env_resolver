import pytest
from fr_common.temp import ScopedTempDir
from pathlib import Path
import os
from fr_env_resolver import ToolUpdater, ManifestUpdater, EnvUpdater, EnvResolver
from fr_env_resolver.structs import Tool, Environ


@pytest.fixture
def temp_dir():
    temp_dir = ScopedTempDir()
    yield temp_dir.path


@pytest.fixture
def tools_dir(temp_dir):
    tools_path = temp_dir / "tools"
    tools_path.mkdir(parents=True)
    dcc_updater = ToolUpdater(tools_path, "dcc_common", load=False)

    dcc_updater.tools = [
        Tool(
            name="maya",
            environ=Environ(
                workflow="maya",
                packages=["local_maya_install"],
            ),
            category="3D",
            command="maya.exe",
            icon="./icons/icon_maya.png",
            title="Maya",
            description="Launch Maya",
        ),
        Tool(
            name="houdini",
            environ=Environ(
                workflow="houdini",
                packages=["local_houdini_install"],
            ),
            category="3D",
            command="houdinicore.exe",
            icon="./icons/icon_houdini.png",
            title="Houdini",
            description="Launch Houdini Core",
            variants={
                "fx": Tool(
                    environ=Environ(
                        override=True,
                        packages=["houdini_local_install"],
                    ),
                    title="Houdini FX",
                    description="Launch Houdini FX",
                    command="houdinifx.exe",
                )
            },
        ),
        Tool(
            name="nuke",
            environ=Environ(
                workflow="nuke",
                packages=["local_nuke_install"],
            ),
            category="2D",
            command="nukex",
            icon="./icons/icon_nuke.png",
            title="NukeX",
            description="Launch Nuke X",
            variants={
                "nuke": Tool(
                    title="Nuke",
                    description="Launch Nuke",
                    command="nuke",
                ),
                "nuke_studio": Tool(
                    title="Nuke Studio",
                    description="Launch Nuke Studio",
                    command="nuke_studio",
                ),
            },
        ),
    ]

    dcc_updater.commit("Create base DCC tools")

    dev_updater = ToolUpdater(tools_path, "dev_common", load=False)
    dev_updater.tools = [
        Tool(
            name="powershell",
            category="Developer Tools",
            command="start powershell",
            icon="./icons/icon_powershell.png",
            title="Terminal",
            description="Launch system terminal",
        ),
    ]

    dev_updater.commit("Create base dev tools")

    standalone_updater = ToolUpdater(tools_path, "standalone_common", load=False)
    standalone_updater.tools = [
        Tool(
            name="zbrush",
            environ=Environ(
                override=True,
                packages=["local_zbrush_install"],
            ),
            category="3D",
            command="ZBrush",
            icon="./icons/icon_zbrush.png",
            title="Zbrush",
            description="Launch Zbrush",
        ),
    ]

    standalone_updater.commit("Create base standalone tools")

    slating_updater = ToolUpdater(tools_path, "slating_tools", load=False)
    slating_updater.tools = [
        Tool(
            name="slating_tool",
            environ=Environ(
                override=False,
                workflow="slating",
            ),
            category="3D",
            command="slating_tool",
            icon="./icons/icon_slating.png",
            title="Slating",
            description="Launch Slating Tool",
        ),
        Tool(
            name="slate_uploader",
            environ=Environ(
                override=False,
                workflow="slating",
            ),
            category="3D",
            command="slate_uploader",
            icon="./icons/icon_slating.png",
            title="Slating Uploader",
            description="Launch Slating Upload tool",
        ),
    ]

    slating_updater.commit("Create slating tools")

    yield tools_path


@pytest.fixture
def manifests_dir(temp_dir):
    path = temp_dir / "manifests"
    path.mkdir(parents=True)
    BASE = ManifestUpdater(path, "", load=False)
    BASE.set_packages(["fr_common", "fr_env_resolver"])
    BASE.set_packages(["frpublish-0.2.9+<1"], workflow="maya")
    BASE.set_packages(["frpublish-0.2.9+<1"], workflow="houdini")
    BASE.set_packages(["frpublish-0.2.9+<1"], workflow="nuke")
    BASE.commit(message="Create BASE platform", publish=True)

    # Create Manifests
    VP22 = ManifestUpdater(path, "vp22", load=False)
    VP22.set_packages(["python-3.9.7+<3.10", "PySide2-5.15+<5.16", "numpy-1.19+<1.20"])
    VP22.set_packages(["maya-2023+<2024"], workflow="maya")
    VP22.set_packages(["houdini-19.5+<20"], workflow="houdini")
    VP22.set_packages(["nuke-14+<15"], workflow="nuke")
    VP22.commit(message="Create VP22 platform", publish=True)

    VP23 = ManifestUpdater(path, "vp23", load=False)
    VP23.set_packages(["python-3.10+<3.11", "PySide2-5.15+<5.16", "numpy-1.23+<1.24"])
    VP23.set_packages(["maya-2025+<2026"], workflow="maya")
    VP23.set_packages(["houdini-20.0+<21"], workflow="houdini")
    VP23.set_packages(["nuke-15+<16"], workflow="nuke")
    VP23.commit(message="Create VP23 platform", publish=True)

    VP24 = ManifestUpdater(path, "vp24", load=False)
    VP24.set_packages(["python-3.11+<3.12", "PySide6-6.5.3+<6.6", "numpy-1.24+<1.25"])
    VP24.commit(message="Create VP24 platform", publish=True)

    os.environ["FR_MANIFEST_PATH"] = path.as_posix()

    (path / "common").mkdir(exist_ok=True)
    COMMON_CONTEXT = EnvUpdater(path / "common", load=False)
    COMMON_CONTEXT.set_manifest("vp22")
    COMMON_CONTEXT.set_variable("SOME_VAR", "1")  # for example
    COMMON_CONTEXT.set_workflow_data("maya", {"manifest": "vp22"})
    COMMON_CONTEXT.set_workflow_data("houdini", {"manifest": "vp23"})
    COMMON_CONTEXT.set_workflow_data("nuke", {"manifest": "vp23"})
    COMMON_CONTEXT.add_tools(
        ["maya", "houdini", "nuke", "powershell", "zbrush"]
    )  # These are the tools that will be shown to the user
    COMMON_CONTEXT.commit("Create common project context", publish=True)

    yield path


@pytest.fixture
def project_dir(temp_dir: Path, manifests_dir: Path):
    path = temp_dir / "projects" / "TestProjectA"
    path.mkdir(parents=True)
    PROJECT_CONTEXT = EnvUpdater(path, load=False)
    # Parents allow breaking of hierarchy when loading cascades
    PROJECT_CONTEXT.set_parent("${FR_MANIFEST_PATH}/common")
    PROJECT_CONTEXT.set_workflow_data(
        "maya",
        {
            "packages": [
                "usersetup",
                "shelf_creator",
                "menu_creator",
                "QtPy",
                "studiolibrary",
                "dwpicker",
                "ffmpeg",
                "ffmpeg_python",
                "image_plane_mate",
                "masterPlayblast",
                "ANgular",
                "custom_shelf",
                "ml_tools",
                "moko",
                "ragdoll",
                "time_editor_tools",
                "anim_playblast",
                "core",
                "sg_api",
                "kata",
                "frjunkbox-0.0.18+<1",
                "fr_debugger-0.0.1+<1",
            ]
        },
    )
    PROJECT_CONTEXT.set_workflow_data(
        "houdini",
        {"packages": ["hshelf"]},
    )
    PROJECT_CONTEXT.set_workflow_data("slating", {"packages": ["frslatingtool"], "manifest": "vp24"})
    PROJECT_CONTEXT.add_tools(["slating_tool", "slate_uploader"])  # These are the tools that will be shown to the user
    PROJECT_CONTEXT.commit("Create TestProjectA context", publish=True)

    yield path


def test_roundtrip(tools_dir, manifests_dir, project_dir):
    os.environ["FR_TOOL_SEARCH_PATH"] = tools_dir.as_posix()
    resolver = EnvResolver(project_dir)

    tools = resolver.tools()
    assert tools == [
        Tool(
            name="maya",
            category="3D",
            command="maya.exe",
            icon=(tools_dir / "icons/icon_maya.png").resolve().as_posix(),
            title="Maya",
            description="Launch Maya",
            filters=[],
            environ=Environ(
                packages=[
                    "local_maya_install",
                ],
                workflow="maya",
                manifest="",
                variables={},
                override=False,
            ),
            variants={},
            path=tools_dir / "dcc_common.frtool",
        ),
        Tool(
            name="houdini",
            category="3D",
            command="houdinicore.exe",
            icon=(tools_dir / "icons/icon_houdini.png").resolve().as_posix(),
            title="Houdini",
            description="Launch Houdini Core",
            filters=[],
            environ=Environ(
                packages=[
                    "local_houdini_install",
                ],
                workflow="houdini",
                manifest="",
                variables={},
                override=False,
            ),
            variants={
                "fx": Tool(
                    name="fx",
                    category="3D",
                    command="houdinifx.exe",
                    icon=(tools_dir / "icons/icon_houdini.png").resolve().as_posix(),
                    title="Houdini FX",
                    description="Launch Houdini FX",
                    filters=[],
                    environ=Environ(
                        packages=[
                            "houdini_local_install",
                            "local_houdini_install",
                        ],
                        workflow="houdini",
                        manifest="",
                        variables={},
                        override=True,
                    ),
                    variants={},
                    path=tools_dir / "dcc_common.frtool",
                ),
            },
            path=tools_dir / "dcc_common.frtool",
        ),
        Tool(
            name="nuke",
            category="2D",
            command="nukex",
            icon=(tools_dir / "icons/icon_nuke.png").resolve().as_posix(),
            title="NukeX",
            description="Launch Nuke X",
            filters=[],
            environ=Environ(
                packages=[
                    "local_nuke_install",
                ],
                workflow="nuke",
                manifest="",
                variables={},
                override=False,
            ),
            variants={
                "nuke": Tool(
                    name="nuke",
                    category="2D",
                    command="nuke",
                    icon=(tools_dir / "icons/icon_nuke.png").resolve().as_posix(),
                    title="Nuke",
                    description="Launch Nuke",
                    filters=[],
                    environ=Environ(
                        packages=[
                            "local_nuke_install",
                        ],
                        workflow="nuke",
                        manifest="",
                        variables={},
                        override=False,
                    ),
                    variants={},
                    path=tools_dir / "dcc_common.frtool",
                ),
                "nuke_studio": Tool(
                    name="nuke_studio",
                    category="2D",
                    command="nuke_studio",
                    icon=(tools_dir / "icons/icon_nuke.png").resolve().as_posix(),
                    title="Nuke Studio",
                    description="Launch Nuke Studio",
                    filters=[],
                    environ=Environ(
                        packages=[
                            "local_nuke_install",
                        ],
                        workflow="nuke",
                        manifest="",
                        variables={},
                        override=False,
                    ),
                    variants={},
                    path=tools_dir / "dcc_common.frtool",
                ),
            },
            path=tools_dir / "dcc_common.frtool",
        ),
        Tool(
            name="powershell",
            category="Developer Tools",
            command="start powershell",
            icon=(tools_dir / "icons/icon_powershell.png").resolve().as_posix(),
            title="Terminal",
            description="Launch system terminal",
            filters=[],
            environ=Environ(
                packages=[],
                workflow=None,
                manifest="",
                variables={},
                override=False,
            ),
            variants={},
            path=tools_dir / "dev_common.frtool",
        ),
        Tool(
            name="zbrush",
            category="3D",
            command="ZBrush",
            icon=(tools_dir / "icons/icon_zbrush.png").resolve().as_posix(),
            title="Zbrush",
            description="Launch Zbrush",
            filters=[],
            environ=Environ(
                packages=[
                    "local_zbrush_install",
                ],
                workflow=None,
                manifest="",
                variables={},
                override=True,
            ),
            variants={},
            path=tools_dir / "standalone_common.frtool",
        ),
        Tool(
            name="slating_tool",
            category="3D",
            command="slating_tool",
            icon=(tools_dir / "icons/icon_slating.png").resolve().as_posix(),
            title="Slating",
            description="Launch Slating Tool",
            filters=[],
            environ=Environ(
                packages=[],
                workflow="slating",
                manifest="",
                variables={},
                override=False,
            ),
            variants={},
            path=tools_dir / "slating_tools.frtool",
        ),
        Tool(
            name="slate_uploader",
            category="3D",
            command="slate_uploader",
            icon=(tools_dir / "icons/icon_slating.png").resolve().as_posix(),
            title="Slating Uploader",
            description="Launch Slating Upload tool",
            filters=[],
            environ=Environ(
                packages=[],
                workflow="slating",
                manifest="",
                variables={},
                override=False,
            ),
            variants={},
            path=tools_dir / "slating_tools.frtool",
        ),
    ]
    base_environment = resolver.resolve_environment()
    assert base_environment == Environ(
        packages=["fr_common", "fr_env_resolver", "python-3.9.7+<3.10", "PySide2-5.15+<5.16", "numpy-1.19+<1.20"],
        workflow=None,
        manifest="vp22",
        variables={"SOME_VAR": "1"},
        override=False,
    )
    maya_environment = resolver.resolve_environment(resolver.find_tool("maya"))
    assert maya_environment == Environ(
        packages=[
            "fr_common",
            "fr_env_resolver",
            "python-3.9.7+<3.10",
            "PySide2-5.15+<5.16",
            "numpy-1.19+<1.20",
            "frpublish-0.2.9+<1",
            "maya-2023+<2024",
            "usersetup",
            "shelf_creator",
            "menu_creator",
            "QtPy",
            "studiolibrary",
            "dwpicker",
            "ffmpeg",
            "ffmpeg_python",
            "image_plane_mate",
            "masterPlayblast",
            "ANgular",
            "custom_shelf",
            "ml_tools",
            "moko",
            "ragdoll",
            "time_editor_tools",
            "anim_playblast",
            "core",
            "sg_api",
            "kata",
            "frjunkbox-0.0.18+<1",
            "fr_debugger-0.0.1+<1",
            "local_maya_install",
        ],
        workflow="maya",
        manifest="vp22",
        variables={"SOME_VAR": "1"},
        override=False,
    )
    houdini_environment = resolver.resolve_environment(resolver.find_tool("houdini"))
    assert houdini_environment == Environ(
        packages=[
            "fr_common",
            "fr_env_resolver",
            "python-3.10+<3.11",
            "PySide2-5.15+<5.16",
            "numpy-1.23+<1.24",
            "frpublish-0.2.9+<1",
            "houdini-20.0+<21",
            "hshelf",
            "local_houdini_install",
        ],
        workflow="houdini",
        manifest="vp23",
        variables={"SOME_VAR": "1"},
        override=False,
    )
    slating_environment = resolver.resolve_environment(resolver.find_tool("slating_tool"))
    assert slating_environment == Environ(
        packages=[
            "fr_common",
            "fr_env_resolver",
            "python-3.11+<3.12",
            "PySide6-6.5.3+<6.6",
            "numpy-1.24+<1.25",
            "frslatingtool",
        ],
        workflow="slating",
        manifest="vp24",
        variables={"SOME_VAR": "1"},
        override=False,
    )
