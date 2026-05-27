"""Execution functionality for fr_env_resolver CLI."""

import argparse
import base64
import os
import pickle
import sys

from rez.config import config
from rez.resolved_context import ResolvedContext
from rez.resolver import ResolverStatus
from rez.system import system

from .parse import Args
from .resolve import ExecutionContext
from ... import constants


def execute(args: Args, execution_context: ExecutionContext) -> None:
    """Execute the resolved environment.

    Args:
        args: Parsed command line arguments
        execution_context: Resolved execution context
    """
    # Process environment variables
    env_pairs = []
    if args.env:
        parser = argparse.ArgumentParser()
        for env_str in args.env:
            if "=" not in env_str:
                parser.error(f"Invalid environment variable format: {env_str}. Must be KEY=VALUE")
            key, value = env_str.split("=", 1)
            if not key:
                parser.error(f"Empty environment variable key in: {env_str}")
            env_pairs.append((key, value))

    # Handle command parsing
    argv = sys.argv[1:]
    command = None
    if "--" in argv:
        command = " ".join(argv[argv.index("--") + 1 :])

    post_command = None
    if command and args.launch:
        post_command = command
        command = None

    if args.launch and execution_context.tool_obj:
        command = execution_context.tool_obj.command

    # Get package paths from environment variables set by fr_env_config
    package_paths = []
    production_paths = os.getenv(constants.ENV.REZ_PRODUCTION_PATHS, "").split(os.pathsep)
    package_paths.extend([p for p in production_paths if p])

    if args.staging or args.dev:
        staging_paths = os.getenv(constants.ENV.REZ_STAGING_PATHS, "").split(os.pathsep)
        package_paths.extend([p for p in staging_paths if p])

    if args.dev:
        dev_paths = os.getenv(constants.ENV.REZ_DEV_PATHS, "").split(os.pathsep)
        package_paths.extend([p for p in dev_paths if p])

    packages = execution_context.environment.packages
    if args.add:
        for add_group in args.add:
            packages += add_group

    if not args.launch:
        # Add the core packages required to make the sub resolvers work if not immediately launching
        core_packages = constants.CORE_PACKAGES
        if core_packages:
            packages.extend(core_packages)

    if args.verbose:
        print("Loading Environment:")
        print(f"  packages: {', '.join(packages)}")
        print("  package_paths:")
        for path in package_paths:
            print(f"    {path}")
        print(f"  time: {args.time}")
        print(f"  dev: {args.dev}")
        print(f"  staging: {args.staging}")

    resolve_time = args.time
    if resolve_time and resolve_time.isdigit():
        resolve_time = int(resolve_time)

    resolved_context = ResolvedContext(
        package_requests=packages,
        package_paths=package_paths,
        timestamp=resolve_time,
        verbosity=1 if args.verbose else 0,
    )

    if resolved_context.status != ResolverStatus.solved:
        print("Failed to resolve env command")
        print(f"rez-env {' '.join(p for p in packages)}")
        print("Info:")
        resolved_context.print_info()
        try:
            from rez.utils.graph_utils import view_graph

            g = resolved_context.graph(as_dot=True)
            view_graph(g)  # TODO: Show this in the UI
        except Exception as e:
            print(f"Failed to show resolve graph, check dot is available: {e}")
        raise RuntimeError(
            "Context failed to resolve, there is likely a package conflict, contact Pipeline for assistance"
        )

    if args.verbose:
        print("Resolved Packages:")
        for package in resolved_context.resolved_packages:
            print(f"  {package.name} {package.version}")
        print("Environment:")
        for k, v in execution_context.environment.variables.items():
            print(f"  {k}={v}")

    def post_setup(rex):
        """Post-setup callback for resolved context."""
        for each_tool in execution_context.tools:
            # TODO: pickled data to support nested variants
            # tool_data_bytes = pickle.dumps(each_tool)
            # encoded = base64.b64encode(tool_data_bytes).decode("latin-1")
            s = "python -m fr_env_resolver "
            # Add context
            if args.context:
                s += " ".join(f'"{c}"' for c in args.context)
            s += f' --tool "{each_tool.name}" --launch'
            if args.dev:
                s += " --dev"
            if args.staging:
                s += " --staging"
            if args.time:
                s += f" --time {args.time}"
            if args.workflow:
                s += f" --workflow {args.workflow}"
            rex.alias(each_tool.name.replace(" ", "_"), s)
            if args.verbose:
                print(f"  alias: {each_tool.name.replace(' ', '_')} -> {s}")

        for k, v in execution_context.environment.variables.items():
            v = rex.expandvars(str(v), format=True)
            if k in ("PATH", "PYTHONPATH"):
                rex.appendenv(k, v)
            else:
                rex.setenv(k, v)

        for key, value in env_pairs:
            rex.setenv(key, value)

        if hasattr(execution_context.context, "as_dict"):
            for k, v in execution_context.context.as_dict().items():
                rex.setenv(f"FR_{k.upper()}", v)

        if hasattr(execution_context.context, "path"):
            rex.setenv("FR_ENV_CONTEXT", execution_context.context.path().as_posix())

        project_code = execution_context.production_info.project_code or getattr(
            execution_context.context, "project_code", ""
        )

        rex.setenv("FR_PRODUCTION_API_NAME", execution_context.production_info.api_name or "")
        rex.setenv("FR_PRODUCTION_API_URL", execution_context.production_info.url or "")
        rex.setenv("FR_PROJECT_CODE", project_code)
        rex.setenv("FR_SHOW", project_code)

        if args.tool:
            rex.setenv("FR_ENV_TOOL", args.tool)
        if args.workflow:
            rex.setenv("FR_ENV_WORKFLOW", args.workflow)
        if args.context_variant:
            rex.setenv("FR_ENV_CONTEXT_VARIANT", args.context_variant)
        if args.tool_variant:
            rex.setenv("FR_ENV_TOOL_VARIANT", args.tool_variant)
        if args.dev:
            rex.setenv("FR_ENV_DEV", "1")
        if args.staging:
            rex.setenv("FR_ENV_STAGING", "1")
        if args.time:
            rex.setenv("FR_ENV_TIME", args.time)

    if post_command:
        if command:
            command = ";".join([command, post_command])
        else:
            command = post_command

    tool_names = [t.name for t in execution_context.tools]
    if args.verbose:
        print("fr_env_resolver loaded")
        if hasattr(execution_context.context, "path"):
            print(f"  context: {execution_context.context.path().as_posix()}")
        if args.dev:
            print("  using developer packages")
        if args.staging:
            print("  using staging packages")
    if command:
        print(f"  Running: {command}")
    else:
        print(f"  Available Tools: {', '.join(tool_names) if tool_names else 'None'}")

    code, _, _ = resolved_context.execute_shell(
        shell=config.default_shell or system.shell,
        norc=False,
        parent_environ={
            k: v for k, v in os.environ.items() if k.upper() not in ("PYTHON_ROOT", "PYTHONHOME", "PYTHON_EXECUTABLE")
        },
        command=command,
        stdin=False,
        quiet=False,
        start_new_session=True,
        detached=False,
        actions_callback=post_setup,
        block=True,
    )
    sys.exit(code)
