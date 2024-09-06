"""
This module is used to manage the scoreboard. It is used to manage the
scoreboard and display the games on the scoreboard. The scoreboard can
be displayed in basic, dual, detailed, or gamecast mode. The basic mode
displays the score and inning of the game. The dual mode displays two
games side by side. The detailed mode displays the score, inning, count,
runners, and umpire details. The gamecast mode displays a detailed view
of the game that includes the score, inning, count, runners, umpire
details, run expectancy, win probability, pitch details, hit details,
and more. The scoreboard can be switched between modes by changing the
mode attribute of the Scoreboard object. The new mode is stored in the
new_mode attribute. The start method is used to start the scoreboard.
The start method loops through the games and displays them on the
scoreboard. If the mode is set to gamecast, the gamecast is displayed
on the scoreboard. If the mode is changed, the scoreboard is cleared
and the new mode is set. If an invalid mode is passed, a ValueError is
raised. The acceptable modes are basic, dual, detailed, and gamecast.
"""

from typing import List, Union
from on_deck.display_manager import DisplayManager
from on_deck.all_games import AllGames
from on_deck.gamecast import Gamecast

class Scoreboard:
    """
    This class is used to manage the scoreboard

    Raises:
        ValueError: If an invalid mode is passed
    """
    _acceptable_modes = ('basic', 'dual', 'detailed', 'gamecast')
    def __init__(self, games: List[dict], mode: str = 'dual'):
        self.games: List[dict] = games
        self.mode: str = mode
        self._new_mode: str = mode

        self.display_manager = DisplayManager()

        self.all_games = AllGames(self.display_manager, games, mode)
        self.gamecast = Gamecast(self.display_manager, games)

    @property
    def new_mode(self):
        """
        This property is used to get the new mode of the scoreboard.

        Returns:
            ValueError: If an invalid mode is passed
        """
        return self._new_mode

    @new_mode.setter
    def new_mode(self, value: Union[str, None]) -> Union[str, None]:
        if value is None:
            return None
        if value not in Scoreboard._acceptable_modes:
            raise ValueError(f'Invalid mode: {value}')
        self._new_mode = value
        return value

    def start(self):
        """This method is used to start the scoreboard"""
        while True:
            if self.mode == 'gamecast':
                self.gamecast.print_gamecast()

            self.all_games.loop(self.mode)

            if self.mode != self.new_mode:
                self.mode = self.new_mode
                self.display_manager.clear_section(0, 0, 384, 256)