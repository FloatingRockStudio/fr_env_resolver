# Copyright (C) 2024 Floating Rock Studio Ltd
"""Base updater implementation."""

import logging
import typing
from pathlib import Path

from fr_config import ConfigWriter, ConfigLoader
from fr_config import constants as config_constants
from fr_config import tagging

from ...interfaces import IEnvUpdater

logger = logging.getLogger("fr_env_resolver.update.base")


class EnvUpdaterBase(IEnvUpdater):
    """API to create and update environments and manifests

    Args:
        config_key(str)  CONFIG_KEY.CONTEXT or CONFIG_KEY.MANIFEST
        path(Context) path to manage
        variant(str) Optional variant
        load(bool) Load the existing data if available
    """

    def __init__(self, config_key: str, path, variant: str = None, load: bool = True):
        path = Path(path)
        if [p.exists() for p in path.parents].count(True) < 1:
            raise IOError(
                "Path is invalid, is it a context? use Context.from_path(path).path() to get the path, ensure at least "
                f"one of the parents exist on the filesystem: {path.as_posix()}"
            )
        context_config = ConfigWriter(config_key, path, variant=variant)
        self._config_key = config_key
        self._path = context_config.path  # Let the config resolve the true path
        self._variant = variant
        if load:
            context_config.load()

        self._changed_configs = set()
        self._configs = {config_key: context_config}

    def _get_config(self, name: str) -> ConfigWriter:
        """Get the config object

        Args:
            name(str)

        Returns:
            ConfigWriter
        """
        return self._configs[name]

    def set_workflow_data(self, workflow: str, data):
        """Set the raw data for the wofklow"""
        self._get_config(self._config_key).set_data(f"workflows/{workflow}", data)

    def get_packages(self, workflow: str = None):
        """Get package list

        Returns:
            list packages
        """
        if workflow:
            return self._get_config(self._config_key).get_data(f"workflows/{workflow}/packages")
        return self._get_config(self._config_key).get_data("packages")

    def get_variables(self, workflow: str = None):
        """Get variables
        Returns:
            dict variables
        """
        if workflow:
            return self._get_config(self._config_key).get_data(f"workflows/{workflow}/variables")
        return self._get_config(self._config_key).get_data("variables")

    def set_packages(self, packages, workflow: str = None):
        """Set packages

        Args:
            packages(List[str])
        """
        config = self._get_config(self._config_key)
        if workflow:
            config.set_data(f"workflows/{workflow}/packages", packages)
        else:
            config.set_data("packages", packages)
        self._changed_configs.add(config.name)

    def set_variables(self, variables, workflow: str = None):
        """Set variables

        Args:
            variables(Dict[str, str])
        """
        config = self._get_config(self._config_key)
        if workflow:
            config.set_data(f"workflows/{workflow}/variables", variables)
        else:
            config.set_data("variables", variables)
        self._changed_configs.add(config.name)

    def remove_variable(self, key: str, workflow: str = None):
        """Remove a variable

        Args:
            key(str)
        Returns:
            bool removed
        """
        config = self._get_config(self._config_key)
        key_path = f"workflows/{workflow}/variables/{key}" if workflow else f"variables/{key}"
        if config.remove_key(key_path):
            self._changed_configs.add(config.name)
            return True
        return False

    def set_variable(self, key: str, value: str, append: bool = False, prepend: bool = False, workflow: str = None):
        """Set a variable

        Args:
            key(str)
            value(str)
            append(bool)
            prepend(bool)
        """
        key_path = f"workflows/{workflow}/variables/{key}" if workflow else f"variables/{key}"
        if not isinstance(value, (str, bytes)):
            raise ValueError(f"Value for {key} must be a str, got {type(value)}")
        if append and prepend:
            raise ValueError("Only append or prepend may be specified")
        if append:
            cascade = config_constants.CASCADE.APPEND
        elif prepend:
            cascade = config_constants.CASCADE.PREPEND
        else:
            cascade = config_constants.CASCADE.REPLACE
        data = {"value": value, "cascade": cascade}
        config = self._get_config(self._config_key)
        config.set_data(key_path, data)
        self._changed_configs.add(config.name)

    def set_parent(self, path: str):
        """Sets env parent target

        Args:
            path(str)
        """
        for name, config in self._configs.items():
            config.set_data("$parent", path)
            self._changed_configs.add(name)

    def commit(
        self, message: str, publish: bool = False, output_dir: typing.Optional[Path] = None
    ) -> typing.Dict[str, Path]:
        """Commit the data

        Args:
            message(str)
            publish(bool): If True will tag as published
            output_dir(str): Optional target dir
        Returns:
            dict[str, Path] where keys in tool, context
        """
        paths = {}
        configs = [c for n, c in self._configs.items() if n in self._changed_configs]
        for config in configs:
            paths[config.name] = config.commit(message, publish=False, output_dir=output_dir)
            tagging.set_tag(paths[config.name], config_constants.TAGS.WIP)

        if publish:
            # Verify that it loads
            for config in configs:
                try:
                    ConfigLoader(
                        config.name,
                        self._path,
                        variant=self._variant,
                        tags=[config_constants.TAGS.LATEST, config_constants.TAGS.PUBLISHED, config_constants.TAGS.WIP],
                    )
                except Exception as e:
                    tagging.set_tag(paths[config.name], config_constants.TAGS.BROKEN)  # We can't use this version
                    raise IOError(f"Config did not save correctly: {paths[config.name].as_posix()}, {e}") from e

            for config in configs:
                tagging.remove_tag(paths[config.name], config_constants.TAGS.WIP)
                tagging.set_tag(paths[config.name], config_constants.TAGS.PUBLISHED)

        return paths
