# Copyright (C) 2024 Floating Rock Studio Ltd
"""Protocols and interfaces for fr_env_resolver."""

from typing import Protocol, Optional, List, Dict, Any
from pathlib import Path

from .structs import Tool, Environ, ProductionInfo


class IResolver(Protocol):
    """Protocol for environment resolvers."""

    def tools(self) -> List[Tool]:
        """Get all available tools.

        Returns:
            List of Tool objects available in this context.
        """
        ...

    def find_tool(self, name: str, variant: Optional[str] = None) -> Optional[Tool]:
        """Find a specific tool by name and variant.

        Args:
            name: Tool name to find
            variant: Optional variant name

        Returns:
            Tool object if found, None otherwise.
        """
        ...

    def resolve_environment(
        self, tool: Optional[Tool] = None, workflow: Optional[str] = None, manifest: Optional[str] = None
    ) -> Environ:
        """Resolve the environment for given parameters.

        Args:
            tool: Optional tool to include in environment
            workflow: Optional workflow to apply
            manifest: Optional manifest to use

        Returns:
            Resolved environment with packages and variables.
        """
        ...

    def production_info(self) -> ProductionInfo:
        """Get production information for this context.

        Returns:
            ProductionInfo object with API details.
        """
        ...


class IEnvUpdater(Protocol):
    """Protocol for environment updaters."""

    def commit(self, message: str) -> Path:
        """Save changes with a commit message.

        Args:
            message: Commit message describing changes

        Returns:
            Path to the saved configuration file.
        """
        ...

    def set_data(self, key: str, value: Any) -> None:
        """Set configuration data for a key.

        Args:
            key: Configuration key
            value: Value to set
        """
        ...

    def get_data(self, key: str) -> Any:
        """Get configuration data for a key.

        Args:
            key: Configuration key

        Returns:
            Configuration value.
        """
        ...


class IToolUpdater(Protocol):
    """Protocol for tool collection updaters."""

    tools: List[Tool]

    def commit(self, message: str) -> Path:
        """Save the tool collection.

        Args:
            message: Commit message

        Returns:
            Path to created file.
        """
        ...
