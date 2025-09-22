# Copyright (C) 2024 Floating Rock Studio Ltd
"""Environment resolver implementation."""

from __future__ import annotations
import os
import re
import copy
import logging
from collections import deque
from pathlib import Path
from typing import List, Optional

from fr_config import ConfigLoader, constants as _config_constants

from ... import constants
from ...interfaces import IResolver
from ...structs import Tool, Environ, ProductionInfo
from ..core import resolve as _resolve

logger = logging.getLogger("fr_env_resolver.resolve")


class EnvResolver(IResolver):
    """Environment resolver implementation.

    Args:
        path: Path to load from
        variant: Optional variant to load
    """

    def __init__(self, path: str | Path, variant: Optional[str] = None):
        path = Path(path)
        if [p.exists() for p in path.parents].count(True) < 2:
            raise IOError(
                "Path is invalid, is it a context? use Context.from_path(path).path() to get the path, ensure at least "
                f"one of the parents exist on the filesystem: {path.as_posix()}"
            )
        self._variant = variant or constants.DEFAULT_VARIANT

        logger.info(f"EnvResolver: path={path}, variant={self._variant}")

        self._tool_config = ConfigLoader(constants.CONFIG_KEY.TOOL, path, variant=self._variant)
        self._context_config = ConfigLoader(constants.CONFIG_KEY.CONTEXT, path, variant=self._variant)
        self._path = self._tool_config.path  # Let the config resolve the true path

        logger.debug(f"Loaded configs:")
        logger.debug(f"  Tool config loaded paths: {self._tool_config.loaded_paths()}")
        logger.debug(f"  Context config loaded paths: {self._context_config.loaded_paths()}")

        self._environ_cache = None
        self._tool_cache = None
        self._manifest_cache = {}  # {manifest: Config}  # variant is implied as it's the same for all here

    def production_info(self) -> ProductionInfo:
        """Get production information for this context.

        Returns:
            ProductionInfo object with API details.
        """
        api_info = self._context_config.value("production_info")
        return ProductionInfo(
            api_name=api_info.get("api_name") or "",
            url=api_info.get("url") or None,
            project_code=api_info.get("project_code") or None,
        )

    # MARK: Manifest
    def _manifest(self, manifest: str, workflow: str = "default") -> Environ:
        """Get manifest environment.

        Args:
            manifest: Manifest name
            workflow: Workflow name

        Returns:
            Environ object for the manifest.
        """
        workflow = workflow or "default"
        if manifest in self._manifest_cache:
            if workflow in self._manifest_cache[manifest]:
                return self._manifest_cache[manifest][workflow]
            return self._manifest_cache[manifest]["default"]

        # Find the manifest
        manifest_path = os.getenv(constants.ENV.MANIFEST_PATH)
        if not manifest_path:
            raise RuntimeError(f"{constants.ENV.MANIFEST_PATH} is not set, cannot find platform: {manifest}")

        path = f"{manifest_path}/{manifest.strip('/')}"
        if not os.path.exists(path):
            raise RuntimeError(f"manifest ({manifest}) cannot be found on path: {manifest_path}")

        logger.debug(f"Loading manifest config from: {path}")

        manifest_config = ConfigLoader(constants.CONFIG_KEY.MANIFEST, path, variant=self._variant)

        logger.debug(f"Manifest config loaded paths: {manifest_config.loaded_paths()}")

        variables = manifest_config.value("variables")
        packages = manifest_config.value("packages")
        # override = manifest_config.value("override")
        override = False

        logger.debug(f"Manifest variables={variables}, packages={packages}")

        manifests = {
            "default": Environ(override=override, variables=variables, packages=packages, workflow="", manifest="")
        }
        for workflow_name, workflow_data in manifest_config.value("workflows").items():
            manifests[workflow_name] = Environ(
                override=workflow_data["override"],
                variables=workflow_data["variables"],
                packages=workflow_data["packages"],
                workflow="",
                manifest="",
            )
            if not workflow_data["override"]:
                manifests[workflow_name] = self._resolve_environ(manifests["default"], manifests[workflow_name])
        if workflow in manifests:
            return manifests[workflow]
        return manifests["default"]

    def _environ(self) -> Environ:
        """Get base environment from context config.

        Returns:
            Base Environ object.
        """
        if self._environ_cache:
            return self._environ_cache
        variables = self._context_config.value("variables")
        packages = self._context_config.value("packages")
        manifest = self._context_config.value("manifest")

        logger.debug(f"_environ: variables={variables}, packages={packages}, manifest={manifest}")

        self._environ_cache = Environ(
            override=False, variables=variables, packages=packages, workflow="", manifest=manifest
        )
        return self._environ_cache

    # MARK: Resolve
    def _resolve_environ(self, base: Environ, other: Environ) -> Environ:
        """Resolve two environments together.

        Args:
            base: Base environment
            other: Environment to merge

        Returns:
            Merged environment.
        """
        if other.override:
            logger.debug(f"_resolve_environ: other.override=True, returning other.packages={other.packages}")
            return other

        environ = Environ()
        if base.packages and other.packages:
            environ.packages = copy.copy(base.packages)

            compare_pattern = r"^(?:[!~]*)([_a-zA-Z0-9]+)-?.*?"

            for new_pkg in other.packages:
                # Find if there's already a package with the same "name" (using compare regex)
                new_match = re.match(compare_pattern, new_pkg)
                if new_match:
                    new_name = new_match.group(1)
                    # Look for existing package with same name
                    replaced = False
                    for i, existing_pkg in enumerate(environ.packages):
                        existing_match = re.match(compare_pattern, existing_pkg)
                        if existing_match and existing_match.group(1) == new_name:
                            # Replace existing package
                            environ.packages[i] = new_pkg
                            replaced = True
                            break
                    if not replaced:
                        # No existing package with same name, append
                        environ.packages.append(new_pkg)
                else:
                    # Couldn't parse package name, just append if not already present
                    if new_pkg not in environ.packages:
                        environ.packages.append(new_pkg)

            logger.debug(
                f"_resolve_environ: Merging base.packages={base.packages} + other.packages={other.packages} = {environ.packages}"
            )
        elif other.packages:
            environ.packages = copy.copy(other.packages)
            logger.debug(f"_resolve_environ: Using other.packages={other.packages}")
        elif base.packages:
            environ.packages = copy.copy(base.packages)
            logger.debug(f"_resolve_environ: Using base.packages={base.packages}")
        else:
            logger.debug(f"_resolve_environ: No packages from either base or other")

        if base.variables and other.variables:
            environ.variables = self._context_config.static_resolve_value("/variables", base.variables, other.variables)
        elif base.variables:
            environ.variables = copy.copy(base.variables)
        elif other.variables:
            environ.variables = copy.copy(other.variables)

        environ.override = other.override
        environ.workflow = other.workflow or base.workflow
        environ.manifest = other.manifest or base.manifest
        if not environ.workflow:
            environ.workflow = None

        return environ

    def resolve_environment(
        self, tool: Optional[Tool] = None, workflow: Optional[str] = None, manifest: Optional[str] = None
    ) -> Environ:
        """Resolve an environment for a tool.

        Args:
            tool: Optional tool to load
            workflow: Optional workflow to use
            manifest: Optional manifest to use

        Returns:
            Resolved environment.
        """
        workflow = workflow or (tool.environ.workflow if tool else None)
        if not workflow:
            workflow = "default"

        logger.debug(
            f"resolve_environment: tool={tool.name if tool else None}, workflow={workflow}, manifest={manifest}"
        )

        if tool and tool.environ.override:
            logger.debug(f"Tool has override=True, using tool environment exclusively")
            if tool.environ.manifest:
                manifest_env = self._manifest(tool.environ.manifest, workflow)
                base = self._resolve_environ(manifest_env, self._environ())
            else:
                base = self._environ()

            result = copy.deepcopy(self._resolve_environ(base, tool.environ))
            logger.debug(f"Final resolved environment (override): packages={result.packages}")
            return result

        workflow_path = f"/workflows/{workflow}" if workflow else ""

        resolve_stack = deque()
        base_environ = Environ(
            packages=self._context_config.value("packages"),
            variables=self._context_config.value("variables"),
            manifest=self._context_config.value("manifest"),
            override=False,
        )

        logger.debug(f"Base environment: packages={base_environ.packages}, manifest={base_environ.manifest}")

        resolve_stack.append(base_environ)
        if workflow:
            workflow_data = self._context_config.value(workflow_path)
            logger.debug(f"Workflow '{workflow}' data: {workflow_data}")
            workflow_environ = _resolve.dict_to_dataclass(workflow_data, Environ)
            logger.debug(f"Workflow environment: packages={workflow_environ.packages}")
            resolve_stack.append(workflow_environ)
        if not manifest or manifest.startswith("./"):
            submanifest = None
            if manifest:
                submanifest = manifest.lstrip("./")
                manifest = None
            if tool:
                manifest = tool.environ.manifest

            if not manifest:
                for each in reversed(resolve_stack):
                    manifest = each.manifest
                    if manifest:
                        break

            if submanifest and manifest:
                manifest = f"{manifest}/{submanifest}"

        if manifest:
            logger.debug(f"Loading manifest: {manifest}")
            manifest_environ = self._manifest(manifest, workflow)
            logger.debug(f"Manifest environment: packages={manifest_environ.packages}")
            resolve_stack.appendleft(manifest_environ)

        if tool and not tool.environ.is_default():
            logger.debug(f"Adding tool environment: packages={tool.environ.packages}")
            resolve_stack.append(tool.environ)

        logger.debug(f"Resolve stack size: {len(resolve_stack)}")
        for i, env in enumerate(resolve_stack):
            logger.debug(f"  [{i}] packages={env.packages}, manifest={env.manifest}, override={env.override}")

        result = resolve_stack.popleft()
        for each in resolve_stack:
            logger.debug(f"Merging: base.packages={result.packages} + other.packages={each.packages}")
            result = self._resolve_environ(result, each)
            logger.debug(f"Result after merge: packages={result.packages}")

        logger.debug(f"Final resolved environment: packages={result.packages}")
        return result

    # Mark: Tools
    def find_tool(self, name: str, variant: Optional[str] = None) -> Optional[Tool]:
        """Find a tool if it exists.

        Args:
            name: Tool name to find
            variant: Optional variant path

        Returns:
            Tool object if found, None otherwise.
        """
        try:
            for tool in self.tools():
                if tool.name == name:
                    break
            else:
                return None

            if variant:
                parent = tool
                for each in variant.strip("/").split("/"):
                    for variant_name, tool_variant in parent.variants.items():
                        if variant_name == each:
                            parent = tool_variant
                            break
                    else:
                        return None
                return copy.deepcopy(parent)
            return copy.deepcopy(tool)
        except Exception:
            return None

    def tools(self) -> List[Tool]:
        """Return all available tools for this context.

        Returns:
            List of Tool objects.
        """
        tools = self._tool_config.value("tools")
        if not tools:
            return []
        if self._tool_cache:
            return copy.deepcopy(self._tool_cache)
        # Get the base tools
        descriptors = {}
        for tool in _resolve.find_tools():
            if tool.name in descriptors:
                logger.warning(f"Multiple descriptors found for frtool: {tool.name}")
            else:
                descriptors[tool.name] = tool

        result = []
        for name, tool in tools.items():
            descriptor = descriptors.get(name)
            if not descriptor:
                logger.warning(f"Tool has no descriptor: {name} (available: {[k for k in descriptors]})")
                continue
            tool["name"] = name
            if descriptor:
                tool["path"] = descriptor.path
            item = _resolve.resolve_tool(tool, descriptor=descriptor)
            if item:
                result.append(item)
            else:
                logger.warning(f"Tool failed to resolve: {name}")
        self._tool_cache = result
        return copy.deepcopy(self._tool_cache)

    # MARK: Debug
    def dump(self) -> str:
        """Output the data to a printable string.

        Returns:
            Formatted string representation of the resolver state.
        """
        lines = [
            "Resolved Environment",
            "=" * 50,
            f"Context = {self._path}",
            f"Variant = {self._variant}",
        ]
        lines += [
            "=" * 50,
            "Tool Config Paths:",
            f"  Tool: {', '.join(str(p) for p in self._tool_config.loaded_paths())}",
            f"  Context: {', '.join(str(p) for p in self._context_config.loaded_paths())}",
        ]
        lines += [
            "=" * 50,
            "",
            "Base Environment:",
            "  Packages:",
        ]
        lines += [f"    {p}" for p in self._context_config.value("packages")]
        lines += ["  Variables:"]
        lines += [f"    {k}: {v}" for k, v in self._context_config.value("variables").items()]
        lines += ["=" * 50, "", "Workflows:"]
        for workflow, data in self._context_config.value("workflows").items():
            lines += [f"  {workflow}", f"    Override: {data['override']}", "    Packages:"]
            lines += [f"      {p}" for p in data["packages"]]
            lines += ["    Variables:"]
            lines += [f"      {k}: {v}" for k, v in data["variables"].items()]
            lines += [
                "    " + "-" * 50,
            ]

        lines += ["=" * 50, "", "Tools:"]
        for tool in self.tools():
            lines += [
                f"  {tool.name}:",
                f"    Command: {tool.command}",
                f"    Icon: {tool.icon}",
                f"    Title: {tool.title}",
                f"    Description: {tool.description}",
                f"    Category: {tool.category}",
                "    Environment:",
            ]
            lines += [
                f"      Workflow: {tool.environ.workflow}",
                f"      Override: {tool.environ.override}",
                "      Packages:",
            ]
            lines += [f"        {p}" for p in tool.environ.packages]
            lines += ["      Variables:"]
            lines += [f"        {k}: {v}" for k, v in tool.environ.variables.items()]
            lines += [
                "    " + "-" * 50,
            ]

        return "\n".join(lines)
