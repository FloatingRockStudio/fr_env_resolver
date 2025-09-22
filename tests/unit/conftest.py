import pytest
import os
from pathlib import Path


def pytest_configure(config):
    """Configure pytest with basic paths for unit tests."""
    # Set up minimal environment for unit tests - same as integration tests
    # but without importing fr_common which might not be available in unit tests
    resource_dir = Path(__file__).parent.parent / "resources"
    assert resource_dir.exists()

    project_dir = resource_dir / "configs" / "Projects"
    assert project_dir.exists()

    # Set up environment variables for tests
    repo_root = Path(__file__).parent.parent.parent
    os.environ["FR_PROJECTS_DIR"] = str(project_dir)
    os.environ["FR_MANIFEST_PATH"] = str(resource_dir / "configs" / "manifests")
    os.environ["FR_TOOL_SEARCH_PATH"] = str(resource_dir / "tool_configs")
    os.environ["FR_ENV_RESOLVER_ROOT"] = str(repo_root)
    os.environ["FR_ENV_RESOLVER_VERSION"] = "0.2.0"
