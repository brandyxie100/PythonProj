"""
Ship Shooter - Configuration and Asset Paths
=============================================
Centralizes asset path resolution so the game works regardless of
the current working directory.
"""

import os

_SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR: str = os.path.join(_SCRIPT_DIR, "asset")


def res(path: str) -> str:
    """Resolve asset path relative to asset/ directory.

    Args:
        path: Filename or relative path (e.g. 'bg3.jpg', 'player.png').

    Returns:
        Absolute path to the asset file.
    """
    return os.path.join(ASSET_DIR, os.path.basename(path))
