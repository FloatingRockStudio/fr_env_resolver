# Copyright (C) 2024 Floating Rock Studio Ltd
from __future__ import annotations
import os
import json
import logging
import pyjson5 as _json5
import typing
import copy
import dacite
from pathlib import Path
from ... import constants
from ...structs import Tool
from dataclasses import is_dataclass, MISSING, asdict

logger = logging.getLogger("fr_env_resolver.resolve.core")


def _recurse_variants(tool: typing.Union[Tool, typing.Dict]):
    # yields variant_name, variant, parent
    if isinstance(tool, Tool):
        for name, variant in tool.variants.items():
            yield name, variant, tool
            yield from _recurse_variants(variant)
    elif isinstance(tool, dict):
        for name, variant in tool.get("variants", {}).items():
            yield name, variant, tool
            yield from _recurse_variants(variant)


def _resolve_dataclass(target, source, skip_fields: typing.List = None):
    for k, data_field in target.__dataclass_fields__.items():
        if skip_fields and data_field in skip_fields:
            # avoids recursion
            continue
        current_value = getattr(target, k)
        new_value = getattr(source, k)
        if new_value is None:
            if k == "icon":
                print("   s is None")
            continue
        default_values = [None]

        if data_field.type == "typing.Optional[str]":
            # Sometimes the resolved default saves as an empty string instead of None
            default_values.append("")
        if data_field.default_factory != MISSING:
            default_values.append(data_field.default_factory())
        elif data_field.default != MISSING:
            default_values.append(data_field.default)

        if current_value in default_values:
            setattr(target, k, new_value)
        elif is_dataclass(current_value):
            _resolve_dataclass(current_value, new_value, skip_fields=skip_fields)
        elif isinstance(current_value, (list, set)):
            setattr(target, k, current_value + [_s for _s in new_value if _s not in current_value])
        elif isinstance(current_value, dict):
            for kv, vv in new_value.items():
                if kv not in current_value:
                    current_value[kv] = vv
                else:
                    _resolve_dataclass(current_value[kv], vv, skip_fields)


def dict_to_dataclass(data, cls: type):
    """Converts a dict to a dataclass if it isn't already of that instance

    Args:
        dict: data to set
        cls: dataclass to map to
    Returns:
        dataclass
    """
    if isinstance(data, cls):
        return data
    return dacite.from_dict(data_class=cls, data=data)


def resolve_tool(data, parent: Tool = None, descriptor: Tool = None) -> Tool:
    """Resolves the data to a tool instance cascading where required
    Args:
        data: data to load
        parent: parent tool for variants
        descriptor: tool description metaclass

    Returns:
        Tool
    """
    # Variants are done manually
    if isinstance(data, Tool):
        data = asdict(data)
    tool_ = {k: v for k, v in data.items() if k not in ("variants",)}
    tool = dict_to_dataclass(tool_, Tool)
    if descriptor:
        if (data.get("icon") or "").startswith("."):
            tool.icon = (descriptor.path.parent / data["icon"]).resolve().as_posix()
        # pylint: disable=E1101
        _resolve_dataclass(tool, descriptor, skip_fields=[Tool.__dataclass_fields__["variants"]])
        if descriptor.variants:
            tool.variants = copy.deepcopy(descriptor.variants)
            for k, v in tool.variants.items():
                variant = resolve_tool(v, parent=tool, descriptor=descriptor.variants[k])
                tool.variants[k] = variant

    if parent:
        # pylint: disable=E1101
        _resolve_dataclass(tool, parent, skip_fields=[Tool.__dataclass_fields__["variants"]])
    # resolve variants
    if data.get("variants"):
        for k, v in data["variants"].items():
            v["name"] = k
            if descriptor and k in descriptor.variants:
                each_base = descriptor.variants[k]
            else:
                each_base = descriptor
            variant = resolve_tool(v, parent=tool, descriptor=each_base)
            tool.variants[k] = variant

    return tool


def resolve_tool_data(name: str, data: dict, path: Path) -> Tool:
    """Resolves raw data from load

    Args:
        name(str) tool name
        data(dict) data to load
        path(Path) path to the frtool collection this came from

    Returns:
        Tool
    """
    descriptor = {k: v for k, v in data.items() if k not in ("__info__",)}
    descriptor["path"] = path
    descriptor["name"] = name
    if "icon" in descriptor and descriptor["icon"].startswith("."):
        descriptor["icon"] = (path.parent / descriptor["icon"]).resolve().as_posix()

    for variant_name, variant, variant_parent in _recurse_variants(descriptor):
        variant["name"] = variant_name
        variant["path"] = path
        if "icon" in variant and variant["icon"].startswith("."):
            variant["icon"] = (path.parent / variant["icon"]).resolve().as_posix()

    tool = dict_to_dataclass(descriptor, Tool)
    # Cleanup nested resolves
    for variant_name, variant, variant_parent in _recurse_variants(tool):
        # pylint: disable=E1101
        _resolve_dataclass(variant, variant_parent, skip_fields=[Tool.__dataclass_fields__["variants"]])

    return tool


def find_tools(
    search_path: typing.Optional[str] = None, collection_name: typing.Optional[str] = None
) -> typing.Generator[Tool, None, None]:
    """Find the tools on the given search path

    Args:
        search_path(str) Optional directory to search
        collection_name(str) optional collection to search for

    Yields:
        Tool
    """
    paths = (search_path or os.getenv(constants.ENV.TOOL_SEARCH_PATH, "")).split(os.pathsep)
    for path in paths:
        path = Path(path)
        paths = [path / f"{collection_name}.frtool"] if collection_name else path.glob("*.frtool")
        for each in paths:
            if not each.exists() or each.name.startswith("_"):
                continue
            try:
                with each.open("r", encoding="UTF-8") as f:
                    data = _json5.load(f)
            except json.JSONDecodeError as e:
                # TODO: log this
                print(f"Failed to read frtool, invalid json data: {path}, {e}")
                continue

            for name, descriptor in data.items():
                if name.startswith("_"):
                    continue
                yield resolve_tool_data(name, descriptor, each)
