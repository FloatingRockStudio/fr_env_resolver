# Copyright (C) 2024 Floating Rock Studio Ltd
"""Tool updater implementation."""

import datetime
import json
import logging
import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import List

from fr_config import ConfigWriter

from ...constants import TOOL_KEYS, REZ_FR_ENV_RESOLVER_VERSION
from ...exceptions import ValidationException
from ...interfaces import IToolUpdater
from ...structs import Tool
from ..core.validate import validate_tool
from ..core.resolve import find_tools

logger = logging.getLogger("fr_env_resolver.update.tool")


def _tool_to_dict(tool: Tool) -> dict:
    """Convert Tool to dictionary representation.

    Args:
        tool: Tool object to convert

    Returns:
        Dictionary representation of the tool.
    """
    data = {}
    for key in TOOL_KEYS:
        if key in ("variants", "environ"):
            continue  # handled later
        value = getattr(tool, key)
        if value:
            data[key] = value

    if not tool.environ.is_default():
        data["environ"] = asdict(tool.environ)

    if tool.variants:
        data["variants"] = {name: _tool_to_dict(variant) for name, variant in tool.variants.items()}
    return data


class ToolUpdater(IToolUpdater):
    """Implementation for creating and updating tool collections.

    Args:
        tool_dir: Target directory for collection
        collection: Name for collection
        load: Optionally load existing data
    """

    tools = None  # type: List[Tool]

    def __init__(self, tool_dir: Path, collection: str, load: bool = True):
        # TODO: Version this?
        self._tool_dir = Path(tool_dir)
        self._collection = collection
        if not re.match("[a-z][_a-z0-9]+", collection, re.IGNORECASE):
            raise ValidationException(f"Collection name is invalid, must be alphanumeric: {collection}")
        self.tools: List[Tool] = []
        if load:
            self.tools = list(find_tools(tool_dir, collection))
        # TODO: For now, we just modify the tool entries, We'll need to make a proper class for this at some point

    def commit(self, message: str) -> Path:
        """Save the tool collection.

        Args:
            message: Commit message

        Returns:
            Path to created file.
        """
        for tool in self.tools:
            validate_tool(tool)

        path = self._tool_dir / f"{self._collection}.frtool"
        data = {}

        data["__info__"] = {
            "author": os.getlogin(),
            "created": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
            "commit_message": str(message),
            "fr_env_resolver_version": REZ_FR_ENV_RESOLVER_VERSION,
        }

        for tool in self.tools:
            data[tool.name] = _tool_to_dict(tool)

        with path.open("w", encoding="UTF-8") as f:
            f.write(json.dumps(data, indent=4))

        return path
