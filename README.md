# fr_env_resolver

Environment and tool resolution for rez-based pipelines.


### Installation

#### Local Installation
If you have the source code locally, navigate to the project directory and install it:

```bash
cd /path/to/fr_env_resolver
pip install .
```

or with rez:

```bash
cd /path/to/fr_env_resolver
rez-pip install .
```

#### Remote Installation
To install directly from this Git repository:

```bash
pip install git+https://github.com/FloatingRockStudio/fr_env_resolver.git
```

or with rez:

```bash
rez-pip install git+https://github.com/FloatingRockStudio/fr_env_resolver.git
```

## What it does

- Resolves environment contexts from project paths
- Manages tool configurations and launches
- Handles package dependencies and workflows
- Built on fr_config for cascading configuration

## Quick start

```bash
# Install
rez env fr_env_resolver

# Resolve environment for a context
fr_env_resolver /project/shots/seq001/shot010

# Launch Maya with context
fr_env_resolver /project/shots/seq001/shot010 --tool maya

# View resolved packages without launching
fr_env_resolver /project/shots/seq001/shot010 --view
```

## Cascading Configs

A Config comprises of a schema (how the data is structured) and the data itself within a file.
To Cascade is to load data from a low level directory and bubble it up until no more data can be found.

For example, we might specify a list of packages for the project, but a specific sequence might have a different version of Maya, and a specific asset might have a different resolution.
We cascade that information together to resolve a final config to use.

Where this becomes tricky is knowing exactly how to cascade different parts of the data. For example, an object should copy value in it’s entirety, but a container should cascade each child value. These are both dicts.

A list may want to append values to the start or end or in the case of resolution we want their to only ever be two values.

A string may be replaced or appended, but in the case of environment paths we want to join the strings with ; on windows and : on linux.
For packages we want to split each package by “-” first to see if the first part exists before appending.

The list goes on, this makes cascades very complex, but also very powerful.

## Environments

Environments are a subset of config cascades specializing around package and tool management, manifests and workflows.

### Context Path Resolve

Contexts are .frconfigs that live in any directory,
When a path is loaded, the variables "cascade" backwards up the tree for a final resolve.

This allows for per shot/asset variations.

It's important to note this is not restricted to production dirs, any directory can be used to cascade.

The process here is the same for Environment Contexts (packages, variables) and Tool Contexts (The subenvironment used by tools in the launcher)

![Context Path Resolve](./docs/context_path_resolve.png)

### Variants

Inside the config resolve is something called "variants",
By default, there is a "default" variant associated with each level in the hierarchy, but additional variants can be added to produce variations such as per department.

These variations are used in anything deriving from fr_config.
Meaning you can have a variant for a context, manifest, workflow or tool.

If a variant is specified to a loader, it will attempt to load that variant any time it is available before loading the default variant.
You cannot skip loading the default, if that is required then leave it blank and only use variants to provide details.

![Context Path Resolve](./docs/config_variants.png)

### Manifest Path Resolve

Manifests follow a similar paridigm but must live under the FR_MANIFEST_PATH variable.
The resulting subpath can be used as a string within a context manifest parameter.

Manifests are resolved after the context resolve, meaning packages will continue to flow from the project to the shot, but the manifest can be overridden resulting in a divergent pathway.

For example, you may have project specific packages, but while the project is on VP22, one sequence may be on VP23 but still require the project packages.

If you do not want this to happen, set the $parent special parameter in the config to override the path resolution.

![Manifest Path Resolve](./docs/manifest_path_resolve.png)

### Tool Descriptor

A Tool descriptor simply lists how a tool should present to the launcher.
This may contain user facing information such as icons and labels, but also any special packages and variables it requires.

Ideally, these should not specify packages but leave that to the workflow that requires them

![Tool Descriptor](./docs/tool_descriptor.png)

### Tool Dataclasses

When looking at the dataclasses themselves (python) below is how they work together:

![Tools](./docs/context_classes.png)


## Usage

### Command Line Interface

```bash
fr_env_resolver [context] [options]
```

Context is the context config path to pass to fr_config.\
While some of the code references short paths (project scene shot, /project/assets/asset_variant), this requires fr_common to work (not supplied at this time). You will have to provide the entire path on disk (eg: C:/projects/Project/Tree/Scene/Shot)

Common options:

- `--tool TOOL`: Load a specific tool, used in conjunction with --launch
- `--tool_variant name`: Variation of tool (eg: houdini core/fx)
- `--launch`: Launches the tool directly
- `--workflow WORKFLOW`: Specify a workflow
- `--view`: Show resolved environment without running
- `--staging`: Include staging packages
- `--dev`: Include development packages
- `--time`: ignore packages released after the given time. Supported formats are: epoch time (eg 1393014494), or relative time (eg -10s, -5m, -0.5h, -10d)
- `--env "KEY=VALUE"`: Add additional environment variables
- `-a PKG [PKG ...]`: Add extra packages
- `-v/--verbose`: Additional logging information

### Python API

```python
from fr_env_resolver import EnvResolver

# Resolve environment
resolver = EnvResolver("/project/path")
env = resolver.resolve_environment()

# Get tools
tools = resolver.tools()
maya = resolver.find_tool("maya")

# Tool management
from fr_env_resolver import ToolUpdater
updater = ToolUpdater("/tools/path", "collection_name")
updater.tools.append(new_tool)
updater.commit("Added tool")
```

## Lexicon

- **Context**: Project location that determines environment
- **Tool**: Launchable application with package requirements
- **Workflow**: Named package set (maya, nuke, etc)
- **Manifest**: Snapshot of specific package versions
- **Variant**: Alternative configuration (dev, staging, etc)

- **Context**: Project location that determines environment
- **Tool**: Launchable application with package requirements
- **Workflow**: Named package set (maya, nuke, etc)
- **Manifest**: Snapshot of specific package versions
- **Variant**: Alternative configuration (dev, staging, etc)
- **Variable** An environment string variable
- **Override** An optional environment parameter used to indicate that the tool, manifest or workflow should not load any prior environments from parents or cascades. For example; photoshop is not a part of the pipeline, so we only want the photoshop package and no additional components.
