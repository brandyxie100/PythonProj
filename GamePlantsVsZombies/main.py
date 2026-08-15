"""
Plants vs Zombies - Entry Point
================================
Launches the game. Run from project root or GamePlantsVsZombies directory:

    python main.py
    # or from PythonProj: python GamePlantsVsZombies/main.py
"""

import pygame as pg

from source.main import main

if __name__ == "__main__":
    main()
    pg.quit()
