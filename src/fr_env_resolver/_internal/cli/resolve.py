"""Resolver functionality for fr_env_resolver CLI."""

import argparse
import base64
import pickle
import sys
import typing
from dataclasses import dataclass
from pathlib import Path

from .parse import Args
from ..impl.resolver import EnvResolver
from ...structs import Tool, ProductionInfo

try:
    from fr_common.structs import Context
except ImportError:
    Context = None


@dataclass(frozen=True)
class ExecutionContext:
    """Execution context containing all resolved data."""

    context: typing.Any
    resolver: typing.Any
    tools: typing.List[Tool]
    tool_obj: typing.Optional[Tool]
    environment: typing.Any
    production_info: typing.Any


def resolve_from_context(args: Args) -> ExecutionContext:
    """Resolve execution context from a normal context path.

    Args:
        args: Parsed command line arguments

    Returns:
        ExecutionContext with resolved data.
    """
    if Context is not None:
        if len(args.context) == 1:
            context = Context.from_input(args.context[0].replace("\\", "/").strip("/"))
        else:
            context = Context(*args.context)
        path = context.path()
    else:
        # Assume args.context is a full path if Context is not available
        if not args.context:
            parser = argparse.ArgumentParser()
            parser.error("Context argument is required if fr_common is not available")
        path = args.context[0]
        context = type("MockContext", (), {"path": lambda: Path(path)})()

    resolver = EnvResolver(path, variant=args.context_variant)

    if args.view:
        print(resolver.dump())
        sys.exit(0)

    tools = resolver.tools()
    tool_obj = None

    if args.tool:
        tool_names = [t.name for t in tools]
        if args.tool not in tool_names:
            parser = argparse.ArgumentParser()
            parser.error(f"Unknown tool: {args.tool} for context: {context}, available tools: {', '.join(tool_names)}")

        if args.tool_variant:
            tool_obj = resolver.find_tool(args.tool, variant=args.tool_variant)
        else:
            tool_obj = resolver.find_tool(args.tool)

    workflow = args.workflow or None
    manifest = None
    if args.staging or args.dev:
        manifest = "./staging"  # This is a placeholder, we need to figure out a better way to handle this.
    environment = resolver.resolve_environment(tool_obj, workflow, manifest)
    production_info = resolver.production_info()

    return ExecutionContext(
        context=context,
        resolver=resolver,
        tools=tools,
        tool_obj=tool_obj,
        environment=environment,
        production_info=production_info,
    )


def resolve_from_pickle(args: Args) -> ExecutionContext:
    """Resolve execution context from pickled tool data.

    Args:
        args: Parsed command line arguments

    Returns:
        ExecutionContext with resolved data.
    """
    try:
        decoded = base64.b64decode(args.tool_data.encode("latin-1"))
        tool_obj = pickle.loads(decoded)
        assert isinstance(tool_obj, Tool), "Tool data must be an instance of fr_env_resolver.structs.Tool"
    except Exception as e:
        raise RuntimeError("Failed to unpickle tool data") from e

    # Allow context to be optionally passed via CLI for env var population
    context = None
    if args.context:
        if Context and len(args.context) == 1:
            context = Context.from_input(args.context[0].replace("\\", "/").strip("/"))
        elif Context:
            context = Context(*args.context)
        else:
            context = type("MockContext", (), {"path": lambda: Path(args.context[0])})()
    else:
        context = getattr(tool_obj, "context", None)

    if context:
        resolver = EnvResolver(context.path(), variant=args.context_variant)
        production_info = resolver.production_info()
    else:
        resolver = None
        production_info = ProductionInfo("unknown", None, None)

    tools = [tool_obj]
    environment = tool_obj.environ

    return ExecutionContext(
        context=context,
        resolver=resolver,
        tools=tools,
        tool_obj=tool_obj,
        environment=environment,
        production_info=production_info,
    )


def resolve(args: Args) -> ExecutionContext:
    """Resolve execution context based on arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        ExecutionContext with resolved data.
    """
    if args.tool_data:
        return resolve_from_pickle(args)
    else:
        return resolve_from_context(args)
