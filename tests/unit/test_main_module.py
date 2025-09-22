"""Unit tests for the simplified __main__.py module."""

import subprocess
import sys
from pathlib import Path


class TestMainModule:
    """Test the simplified main module entry point."""

    def test_main_module_runs(self):
        """Test that the main module can be executed."""
        result = subprocess.run(
            [sys.executable, "-m", "fr_env_resolver", "--help"], capture_output=True, text=True, check=False
        )

        # Should exit successfully and show help
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_main_module_import(self):
        """Test that the main module can be imported."""
        import fr_env_resolver.__main__

        # Should import without error

    def test_main_function_callable(self):
        """Test that the main function from _internal is callable."""
        from fr_env_resolver._internal.cli.main import main

        # Should be callable without error
        assert callable(main)
