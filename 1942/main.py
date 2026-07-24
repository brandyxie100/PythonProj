#!/usr/bin/env python3
"""1942 — Midway Atoll aerial combat. Run from this directory: python main.py"""

from __future__ import annotations

from game import Game


def main() -> None:
    """Boot the campaign."""
    Game().run()


if __name__ == "__main__":
    main()
