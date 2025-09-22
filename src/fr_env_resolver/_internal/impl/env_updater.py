# Copyright (C) 2024 Floating Rock Studio Ltd
"""Environment updater implementation."""
import logging
import typing
from ... import constants
from ...structs import ProductionInfo
from .base_updater import EnvUpdaterBase
from fr_config import ConfigWriter

logger = logging.getLogger("fr_env_resolver.update.env")


class EnvUpdater(EnvUpdaterBase):
    """API to create and update environments

    Args:
        path(Context) path to manage
        variant(str) Optional variant
        load(bool) Load the existing data if available
    """

    def __init__(self, path, variant: str = None, load: bool = True):
        super().__init__(constants.CONFIG_KEY.CONTEXT, path, variant, load)
        tool_config = ConfigWriter(constants.CONFIG_KEY.TOOL, path, variant=variant)
        self._configs[constants.CONFIG_KEY.TOOL] = tool_config
        if load:
            tool_config.load()

    def get_production_info(self) -> ProductionInfo:
        """Get production info

        Returns:
            ProductionInfo
        """
        api_info = self._get_config(constants.CONFIG_KEY.CONTEXT).value("production_info")
        return ProductionInfo(
            api_name=api_info.get("api_name") or "",
            url=api_info.get("url") or None,
            project_code=api_info.get("project_code") or None,
        )

    def set_production_info(self, info: ProductionInfo):
        """Set Production info"""
        config = self._get_config(constants.CONFIG_KEY.CONTEXT)
        data = {
            "api_name": info.api_name or "",
            "url": info.url or "",
            "project_code": info.project_code or "",
        }
        config.set_data("production_info", data)
        self._changed_configs.add(config.name)

    def set_manifest(self, manifest: str, workflow: str = None):
        """Sets env parent target

        Args:
            manifest(str)
        """
        config = self._get_config(constants.CONFIG_KEY.CONTEXT)
        if workflow:
            config.set_data(f"workflows/{workflow}/manifest", manifest)
        else:
            config.set_data("manifest", manifest)
        self._changed_configs.add(config.name)

    def get_tool_data(self, tool_name: str):
        """Get the raw tool data

        Args:
            tool_name(str)
        Returns:
            dict data
        """
        return self._get_config(constants.CONFIG_KEY.TOOL).get_data(f"tools/{tool_name}")

    def set_tool_data(self, tool_name: str, data):
        """Set the raw tool data

        Args:
            tool_name(str)
            data(dict)
        """
        self._get_config(constants.CONFIG_KEY.TOOL).set_data(f"tools/{tool_name}", data)
        self._changed_configs.add(constants.CONFIG_KEY.TOOL)

    def add_tools(self, tool_names: typing.List[str]):
        """Adds some tools with no additional info

        tool_names(List[str])
        """
        config = self._get_config(constants.CONFIG_KEY.TOOL)
        for tool_name in tool_names:
            config.set_data(f"tools/{tool_name}", {})
        self._changed_configs.add(constants.CONFIG_KEY.TOOL)

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool

        Args:
            tool_name(str)
        Returns:
            bool removed
        """
        if self._get_config(constants.CONFIG_KEY.TOOL).remove_key(f"tools/{tool_name}"):
            self._changed_configs.add(constants.CONFIG_KEY.TOOL)
            return True
        return False
