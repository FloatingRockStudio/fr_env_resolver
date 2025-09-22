# Copyright (C) 2024 Floating Rock Studio Ltd
"""Validation functions for fr_env_resolver."""

import logging
import re
from typing import Optional

from ...structs import Tool
from ...exceptions import ValidationException

logger = logging.getLogger("fr_env_resolver.validate")


def validate_tool(tool: Optional[Tool] = None, _parent: str = "") -> None:
    """Validate the tool recursively.

    Args:
        tool: Tool to validate
        _parent: Internal parameter for recursion tracking

    Raises:
        ValidationException: If not valid
    """
    if tool is None:
        raise ValidationException("Tool cannot be None")

    if tool.name is None or tool.name == "":
        raise ValidationException("Tool name is required")

    if " " in tool.name:
        raise ValidationException("Tool name cannot contain whitespace")

    path = "/".join([_parent, tool.name])
    if not re.match("[a-z][_a-z0-9]+", tool.name, re.IGNORECASE):
        raise ValidationException(
            f"Name contains invalid characters, must start with letter and be alphanumeric: {tool.name} for {path}"
        )

    if not _parent:
        # The root tool only
        if not tool.command:
            raise ValidationException(f"{tool.name}.command is empty")
        if not tool.icon:
            raise ValidationException(f"{tool.name}.icon is empty")
        if not tool.category:
            raise ValidationException(f"{tool.name}.category is empty")
        if not tool.title:
            raise ValidationException(f"{tool.name}.title is empty")
        if not tool.description:
            raise ValidationException(f"{tool.name}.description is empty")
    # TODO: Filters

    for variant_name, variant in tool.variants.items():
        variant.name = variant_name
        validate_tool(variant, path)
