"""
Plants vs Zombies - Game Bootstrap
==================================
Initializes the state machine with main menu, level, victory, and lose screens.
"""

from . import constants as c
from . import tool
from .state import level, mainmenu, screen


def main() -> None:
    """Create game controller, register states, and run main loop."""
    game = tool.Control()
    state_dict = {
        c.MAIN_MENU: mainmenu.Menu(),
        c.GAME_VICTORY: screen.GameVictoryScreen(),
        c.GAME_LOSE: screen.GameLoseScreen(),
        c.LEVEL: level.Level(),
    }
    game.setup_states(state_dict, c.MAIN_MENU)
    game.main()
