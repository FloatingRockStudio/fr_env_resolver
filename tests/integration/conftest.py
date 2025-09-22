import pytest
import os
from pathlib import Path


def pytest_configure(config):
    """Configure pytest with resource paths."""
    test_resource_dir = Path(__file__).parent.parent / "resources"
    assert test_resource_dir.exists()

    test_project_dir = test_resource_dir / "configs" / "Projects"
    assert test_project_dir.exists()

    # Set up environment variables for tests
    repo_root = Path(__file__).parent.parent.parent
    os.environ["FR_PROJECTS_DIR"] = str(test_project_dir)
    os.environ["FR_MANIFEST_PATH"] = str(test_resource_dir / "configs" / "manifests")
    os.environ["FR_TOOL_SEARCH_PATH"] = str(test_resource_dir / "tool_configs")
    os.environ["FR_ENV_RESOLVER_ROOT"] = str(repo_root)
    os.environ["FR_ENV_RESOLVER_VERSION"] = "0.2.0"

    # Try to import fr_common to configure paths
    try:
        from fr_common.constants import PATHS

        assert PATHS.PROJECTS == test_project_dir.as_posix()
    except ImportError:
        # fr_common not available, that's ok
        pass


@pytest.fixture
def resource_dir():
    """Get the path to the test resources directory."""
    return Path(__file__).parent.parent / "resources"


@pytest.fixture
def configs_dir(resource_dir):
    """Get the path to the configs directory."""
    return resource_dir / "configs"


@pytest.fixture
def projects_dir(configs_dir):
    """Get the path to the Projects directory."""
    return configs_dir / "Projects"


@pytest.fixture
def manifests_dir(configs_dir):
    """Get the path to the manifests directory."""
    return configs_dir / "manifests"


@pytest.fixture
def tool_configs_dir(resource_dir):
    """Get the path to the tool_configs directory."""
    return resource_dir / "tool_configs"


@pytest.fixture
def shot_context_path(projects_dir):
    """Get the path to a test shot context."""
    return projects_dir / "FR_ENV" / "03_Production" / "Shots" / "SEQ_001" / "0010"


@pytest.fixture
def shot_context_path_0020(projects_dir):
    """Get the path to another test shot context."""
    return projects_dir / "FR_ENV" / "03_Production" / "Shots" / "SEQ_001" / "0020"


@pytest.fixture
def shot_context_path_0030(projects_dir):
    """Get the path to another test shot context."""
    return projects_dir / "FR_ENV" / "03_Production" / "Shots" / "SEQ_001" / "0030"
