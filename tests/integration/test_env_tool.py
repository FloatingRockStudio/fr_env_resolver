from fr_config import Config
from fr_common.structs import Context


def test_raw_config_data():
    config = Config("env_tool", Context.from_path("/FR_ENV/Shots/SEQ_001/0010").path())
    assert len(config.loaded_paths()) == 3
    assert config.path == Context.from_path("/FR_ENV/Shots/SEQ_001/0010").path()
    assert config.tags == ["published", "latest"]
    assert config.variants == ["default"]

    assert config._data == {
        "tools": {
            "maya": {
                "command": None,
                "description": None,
                "environ": {"override": False, "packages": ["extra_package"], "workflow": None, "variables": {}},
                "filters": [],
                "icon": None,
                "title": None,
                "variants": {},
            },
            "slate_uploader": {
                "command": None,
                "description": None,
                "environ": {
                    "override": True,
                    "packages": ["fr_slating_tool", "python-3.9.7"],
                    "workflow": None,
                    "variables": {},
                },
                "filters": [
                    {
                        "$and": [
                            [["context.sequence", "in", ["SEQ_001", "SEQ_002"]]],
                            [["context.project", "is", "FR_ENV"]],
                        ]
                    }
                ],
                "icon": None,
                "title": None,
                "variants": {},
            },
            "slating_tool": {
                "command": None,
                "description": None,
                "environ": {
                    "override": True,
                    "packages": ["fr_slating_tool", "python-3.9.7"],
                    "workflow": None,
                    "variables": {},
                },
                "filters": [
                    ["context.project", "is", "FR_ENV"],
                    ["user.groups", "contains", "techartist"],
                    ["user.groups", "contains", "developer"],
                ],
                "icon": None,
                "title": None,
                "variants": {
                    "pro_mode": {
                        "command": None,
                        "description": None,
                        "environ": {
                            "override": False,
                            "packages": [
                                "custom_pro_package-0.0.1",
                            ],
                            "workflow": None,
                            "variables": {},
                        },
                        "filters": [],
                        "icon": None,
                        "title": None,
                        "variants": {},
                    },
                },
            },
        },
    }
    assert set(config.keys()) == {"tools"}
    assert set(config.key_paths()) == {
        "/tools",
        "/tools/maya",
        "/tools/maya/command",
        "/tools/maya/description",
        "/tools/maya/environ",
        "/tools/maya/filters",
        "/tools/maya/icon",
        "/tools/maya/title",
        "/tools/maya/variants",
        "/tools/slate_uploader",
        "/tools/slate_uploader/command",
        "/tools/slate_uploader/description",
        "/tools/slate_uploader/environ",
        "/tools/slate_uploader/filters",
        "/tools/slate_uploader/icon",
        "/tools/slate_uploader/title",
        "/tools/slate_uploader/variants",
        "/tools/slating_tool",
        "/tools/slating_tool/command",
        "/tools/slating_tool/description",
        "/tools/slating_tool/environ",
        "/tools/slating_tool/filters",
        "/tools/slating_tool/icon",
        "/tools/slating_tool/title",
        "/tools/slating_tool/variants",
        "/tools/slating_tool/variants/pro_mode",
        "/tools/slating_tool/variants/pro_mode/command",
        "/tools/slating_tool/variants/pro_mode/description",
        "/tools/slating_tool/variants/pro_mode/environ",
        "/tools/slating_tool/variants/pro_mode/filters",
        "/tools/slating_tool/variants/pro_mode/icon",
        "/tools/slating_tool/variants/pro_mode/title",
        "/tools/slating_tool/variants/pro_mode/variants",
    }
