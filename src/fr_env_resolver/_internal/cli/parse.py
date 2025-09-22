"""CLI argument parsing for fr_env_resolver."""

import argparse
import sys
import typing
from dataclasses import dataclass, field

try:
    from fr_common.structs import Context
except ImportError:
    # fr_common is not currently open sourced.
    # Context is just a utility class to resolve shortform paths to floating-rocks full paths
    # This will later be released as Silex for full schema based path resolution
    Context = None


@dataclass(frozen=True)
class Args:
    """Command line arguments for fr_env_resolver."""

    add: typing.Optional[typing.List[typing.List[str]]] = None
    dev: bool = False
    staging: bool = False
    launch: bool = False
    view: bool = False
    env: typing.Optional[typing.List[str]] = None
    time: typing.Optional[str] = None
    workflow: str = ""
    tool: str = ""
    tool_variant: str = ""
    context_variant: str = "default"
    tool_data: str = ""
    verbose: bool = False
    log_level: str = "INFO"
    context: typing.List[str] = field(default_factory=list)


def parse_args() -> Args:
    """Parse command line arguments.

    Returns:
        Parsed arguments as Args dataclass.
    """
    parser = argparse.ArgumentParser(prog="fr_env_resolver")
    parser.add_argument("-a", "--add", action="append", dest="add", nargs="+", help="Additional packages to add")
    parser.add_argument("--dev", action="store_true", help="Use developer packages")
    parser.add_argument("--staging", action="store_true", help="Use staging packages")
    parser.add_argument("--launch", action="store_true", help="Launches the specified tool, For internal use")
    parser.add_argument("--view", action="store_true", help="Prints the result of the resolver without running it")
    parser.add_argument("-e", "--env", action="append", help="Set environment variables in KEY=VALUE format")
    parser.add_argument(
        "-t",
        "--time",
        dest="time",
        type=str,
        help="ignore packages released after the given time. Supported formats "
        "are: epoch time (eg 1393014494), or relative time (eg -10s, -5m, "
        "-0.5h, -10d)",
    )
    parser.add_argument(
        "-w",
        "--workflow",
        dest="workflow",
        type=str,
        default="",
        help="Workflow subshell to load, eg: maya",
    )
    parser.add_argument(
        "--tool",
        dest="tool",
        type=str,
        default="",
        help="Tool subshell to load, for internal use",
    )
    parser.add_argument(
        "--tool_variant",
        dest="tool_variant",
        type=str,
        default="",
        help="Tool variant to load, for internal use",
    )
    parser.add_argument(
        "--context_variant",
        dest="context_variant",
        type=str,
        default="default",
        help="Context variant to load",
    )
    parser.add_argument(
        "--tool_data",
        dest="tool_data",
        type=str,
        default="",
        help="Pickled structs.Tool data to load, for internal use",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Prints the resolved environment")
    parser.add_argument(
        "--log-level",
        dest="log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    if Context:
        parser.add_argument(
            "context",
            type=str,
            nargs="*",
            help="Context to load, eg: /project/tree/scene/shot or project tree scene shot",
        )
    else:
        parser.add_argument(
            "context",
            type=str,
            nargs="*",
            help="Context path to load, eg: /full/path/to/context",
        )

    argv = sys.argv[1:]
    if "--" in argv:  # Subsequent args are args to the command being launched
        argv = argv[: argv.index("--")]
    parsed_args = parser.parse_args(argv)

    if parsed_args.verbose and parsed_args.log_level == "INFO":
        parsed_args.log_level = "DEBUG"

    return Args(
        add=parsed_args.add,
        dev=parsed_args.dev,
        staging=parsed_args.staging,
        launch=parsed_args.launch,
        view=parsed_args.view,
        env=parsed_args.env,
        time=parsed_args.time,
        workflow=parsed_args.workflow,
        tool=parsed_args.tool,
        tool_variant=parsed_args.tool_variant,
        context_variant=parsed_args.context_variant,
        tool_data=parsed_args.tool_data,
        verbose=parsed_args.verbose,
        log_level=parsed_args.log_level,
        context=parsed_args.context,
    )
