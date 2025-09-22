# Copyright (C) 2024 Floating Rock Studio Ltd
"""Manifest updater implementation."""

import logging
from pathlib import Path

from ... import constants
from .base_updater import EnvUpdaterBase

logger = logging.getLogger("fr_env_resolver.update.manifest")


class ManifestUpdater(EnvUpdaterBase):
    """Implementation for creating and updating manifests.

    Args:
        manifest_dir: Directory containing manifests
        manifest: Manifest name
        variant: Optional variant
        load: Load the existing data if available
    """

    def __init__(self, manifest_dir: str, manifest: str, variant: str = None, load: bool = True):
        if not Path(manifest_dir).exists():
            raise RuntimeError(f"Manifest dir does not exist: {manifest_dir}")
        path = Path(manifest_dir) / manifest.strip("/")
        if not path.exists():
            path.mkdir(parents=False)
        super().__init__(constants.CONFIG_KEY.MANIFEST, path, variant, load)
