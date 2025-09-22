import pytest
import os
import shutil
import json
from pathlib import Path
from fr_env_resolver import EnvUpdater, ToolUpdater
from fr_env_resolver.exceptions import ValidationException
from fr_env_resolver.structs import Tool, Environ
from fr_common import path as fr_path
from fr_common.temp import ScopedTempDir
from fr_common.structs import Context


@pytest.fixture
def clear_shot():
    path = Path(os.environ["FR_PROJECTS_DIR"]) / "FR_ENV/03_Production/Shots/SEQ_001/0020/"
    for each in list(path.iterdir()):
        shutil.rmtree(each)
    try:
        yield "/FR_ENV/Shots/SEQ_001/0020"
    finally:
        path = Path(os.environ["FR_PROJECTS_DIR"]) / "FR_ENV/03_Production/Shots/SEQ_001/0020/"
        # for each in list(path.iterdir()):
        #     shutil.rmtree(each)


def test_create_context(clear_shot):
    updater = EnvUpdater(Context.from_path(clear_shot).path(), load=True)
    assert updater._configs["env_tool"]._data == {}
    assert updater._configs["env_context"]._data == {}

    # Set some context data
    updater.set_packages(["PySide2-5.15.2", "python-3.9.7"])
    updater.set_variable("SOME_VAR", "2")
    updater.set_variable("PATH", "/path/to/something", append=True)
    # Set the parent
    updater.set_parent("${FR_PROJECTS_DIR}/FR_ENV")

    # Set some tool data
    updater.set_tool_data("maya", {"environ": {"packages": {"cascade": "append", "value": ["extra_package"]}}})

    # Commit
    created_paths = updater.commit("This is a test", publish=True)
    output_dir = updater._configs["env_tool"].path / ".fr_config/env_tool/default"
    assert output_dir.exists()
    output_dir = updater._configs["env_context"].path / ".fr_config/env_context/default"
    assert output_dir.exists()

    # Confirm they have the published tag
    tags = fr_path.get_version_tags(created_paths["env_tool"].parent)
    assert tags == {"v1": ["published"]}
    tags = fr_path.get_version_tags(created_paths["env_context"].parent)
    assert tags == {"v1": ["published"]}
    # validate the data
    print(created_paths)
    with created_paths["env_tool"].open("r") as f:
        data = json.loads(f.read())
        del data["__info__"]["created"]
        assert data == {
            "$parent": "${FR_PROJECTS_DIR}/FR_ENV",
            "tools": {"maya": {"environ": {"packages": {"cascade": "append", "value": ["extra_package"]}}}},
            "__info__": {
                "source": None,
                "version": 1,
                "name": "env_tool",
                "variant": "default",
                "schema": (Path(os.getenv("REZ_FR_ENV_RESOLVER_ROOT")) / "schema/env_tool.fr_schema").as_posix(),
                "author": os.getlogin(),
                "commit_message": "This is a test",
            },
        }

    with created_paths["env_context"].open("r") as f:
        data = json.loads(f.read())
        del data["__info__"]["created"]
        assert data == {
            "packages": ["PySide2-5.15.2", "python-3.9.7"],
            "variables": {
                "SOME_VAR": {"value": "2", "cascade": "replace"},
                "PATH": {"value": "/path/to/something", "cascade": "append"},
            },
            "$parent": "${FR_PROJECTS_DIR}/FR_ENV",
            "__info__": {
                "source": None,
                "version": 1,
                "name": "env_context",
                "variant": "default",
                "schema": (Path(os.getenv("REZ_FR_ENV_RESOLVER_ROOT")) / "schema/env_context.fr_schema").as_posix(),
                "author": os.getlogin(),
                "commit_message": "This is a test",
            },
        }

    # Update the previously set data
    updater = EnvUpdater(Context.from_path(clear_shot).path(), load=True)
    assert updater._configs["env_tool"]._data != {}
    assert updater._configs["env_context"]._data != {}

    # Set some context data
    updater.set_packages(["python-3.10.3"])
    updater.set_variable("SOME_VAR", "1")
    updater.set_variable("OTHER_VAR", "1")

    # Set some tool data
    maya_tool = updater.get_tool_data("maya")
    maya_tool["environ"]["override"] = True
    maya_tool["environ"]["packages"]["value"].append("another_package")
    updater.set_tool_data("maya", maya_tool)

    # Commit
    updated_paths = updater.commit("Update test", publish=True)

    # Confirm they have the published tag
    tags = fr_path.get_version_tags(updated_paths["env_tool"].parent)
    assert tags == {"v2": ["published"]}
    tags = fr_path.get_version_tags(updated_paths["env_context"].parent)
    assert tags == {"v2": ["published"]}

    # validate the data
    with updated_paths["env_tool"].open("r") as f:
        data = json.loads(f.read())
        del data["__info__"]["created"]
        assert data == {
            "$parent": "${FR_PROJECTS_DIR}/FR_ENV",
            "tools": {
                "maya": {
                    "environ": {
                        "packages": {"cascade": "append", "value": ["extra_package", "another_package"]},
                        "override": True,
                    }
                }
            },
            "__info__": {
                "source": created_paths["env_tool"].as_posix(),
                "version": 2,
                "name": "env_tool",
                "variant": "default",
                "schema": (Path(os.getenv("REZ_FR_ENV_RESOLVER_ROOT")) / "schema/env_tool.fr_schema").as_posix(),
                "author": os.getlogin(),
                "commit_message": "Update test",
            },
        }

    with updated_paths["env_context"].open("r") as f:
        data = json.loads(f.read())
        del data["__info__"]["created"]
        assert data == {
            "packages": ["python-3.10.3"],
            "variables": {
                "SOME_VAR": {"value": "1", "cascade": "replace"},
                "OTHER_VAR": {"value": "1", "cascade": "replace"},
                "PATH": {"value": "/path/to/something", "cascade": "append"},
            },
            "$parent": "${FR_PROJECTS_DIR}/FR_ENV",
            "__info__": {
                "source": created_paths["env_context"].as_posix(),
                "version": 2,
                "name": "env_context",
                "variant": "default",
                "schema": (Path(os.getenv("REZ_FR_ENV_RESOLVER_ROOT")) / "schema/env_context.fr_schema").as_posix(),
                "author": os.getlogin(),
                "commit_message": "Update test",
            },
        }


def test_tool_updater():
    temp_dir = ScopedTempDir("fr_env_resolver")
    collection = "test"

    updater = ToolUpdater(str(temp_dir), collection, load=True)
    assert updater.tools == []

    # Create some invalid tools
    updater.tools.append(Tool(name=" space here"))
    with pytest.raises(ValidationException):
        updater.commit("test")
    # Remove invalid tools
    updater.tools = []
    updater.tools.append(
        Tool(
            name="maya",
            environ=Environ(
                workflow="maya",
            ),
            category="3D",
            command="maya.exe",
            icon="./maya_icon.png",
            title="MAYA",
            description="Launch Maya",
            filters=[["os", "is", "windows"]],
        )
    )
    path = updater.commit("test commit")
    with path.open("r", encoding="utf-8") as f:
        result = json.loads(f.read())

    # Remove timestamp
    del result["__info__"]["created"]
    assert result == {
        "__info__": {
            "author": os.getlogin(),
            "commit_message": "test commit",
            "fr_env_resolver_version": os.getenv("REZ_FR_ENV_RESOLVER_VERSION"),
        },
        "maya": {
            "command": "maya.exe",
            "description": "Launch Maya",
            "category": "3D",
            "environ": {
                "override": False,
                "manifest": "",
                "packages": [],
                "variables": {},
                "workflow": "maya",
            },
            "filters": [
                [
                    "os",
                    "is",
                    "windows",
                ],
            ],
            "icon": "./maya_icon.png",
            "title": "MAYA",
        },
    }

    # Load again
    # check still exists
    updater = ToolUpdater(str(temp_dir), collection, load=True)
    assert updater.tools == [
        Tool(
            name="maya",
            environ=Environ(
                workflow="maya",
            ),
            category="3D",
            command="maya.exe",
            icon=(temp_dir / "maya_icon.png").resolve().as_posix(),
            title="MAYA",
            description="Launch Maya",
            filters=[["os", "is", "windows"]],
            path=temp_dir / "test.frtool",
        )
    ]
