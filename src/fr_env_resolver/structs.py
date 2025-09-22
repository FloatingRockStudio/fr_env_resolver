# Copyright (C) 2024 Floating Rock Studio Ltd
"""Data structures for fr_env_resolver."""

from __future__ import annotations
import typing
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Environ:
    """Environment configuration containing packages, variables, and workflow settings.

    This class represents the environment configuration that can be applied
    to resolve package dependencies and environment variables for tools and workflows.

    Attributes:
        packages: List of package names/versions to include in the environment
        workflow: Optional workflow name to apply (e.g., "maya", "houdini")
        manifest: Optional manifest identifier for platform-specific configurations
        variables: Dictionary of environment variables to set
        override: If True, this environment overrides parent configurations completely
    """

    packages: typing.List[str] = field(default_factory=list)
    workflow: typing.Optional[str] = None
    manifest: typing.Optional[str] = ""
    variables: typing.Dict[str, str] = field(default_factory=dict)
    override: bool = False

    def is_default(self) -> bool:
        """Check if this environment is equivalent to the default empty environment.

        Returns:
            True if this environment matches the default Environ(), False otherwise.
        """
        return self == Environ()


@dataclass
class Tool:
    """Represents a launchable tool with its configuration and environment.

    A Tool encapsulates all the information needed to launch and configure
    a specific application or utility within the pipeline environment.

    Attributes:
        name: Unique identifier for the tool
        category: Tool category (e.g., "3D", "2D", "Pipeline")
        command: Command line to execute when launching the tool
        icon: Path to the tool's icon file
        title: Display name for the tool
        description: Human-readable description of the tool
        filters: List of filter conditions for tool availability
        environ: Environment configuration for this tool
        variants: Dictionary of tool variants (e.g., {"test": Tool(...)})
        path: Base path where tool descriptors are located
    """

    name: typing.Optional[str] = None
    category: typing.Optional[str] = None
    command: typing.Optional[str] = None
    icon: typing.Optional[str] = None
    title: typing.Optional[str] = None
    description: typing.Optional[str] = None
    filters: typing.Any = field(default_factory=list)
    environ: Environ = field(default_factory=Environ)
    variants: typing.Dict[str, Tool] = field(default_factory=dict)
    path: typing.Optional[Path] = None


@dataclass
class ProductionInfo:
    """Information about the production environment and APIs.

    Contains metadata about the production context, including API endpoints
    and project identification information.

    Attributes:
        api_name: Name of the production API (e.g., "shotgun", "ftrack")
        url: Optional URL for the production API endpoint
        project_code: Optional project identifier code
    """

    api_name: str
    url: typing.Optional[str]
    project_code: typing.Optional[str]
