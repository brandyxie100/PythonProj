"""Shared pytest fixtures for stickman battle tests."""

from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _pygame_bootstrap() -> None:
    """Initialize pygame modules used by terrain rectangles."""
    pygame.init()
    yield
    pygame.quit()
