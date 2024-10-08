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

import socket
import platform
from typing import List, Union
from on_deck.colors import Colors
from on_deck.fonts import Fonts
from on_deck.display_manager import DisplayManager
from on_deck.all_games import AllGames
from on_deck.gamecast import Gamecast

if platform.system() == 'Windows':
    from RGBMatrixEmulator import RGBMatrixOptions # pylint: disable=E0401
else:
    from rgbmatrix import RGBMatrixOptions # pylint: disable=E0401

def get_ip_address() -> str:
    # Create a socket to get the local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually need to send data; we're just looking for the local IP
        s.connect(('8.8.8.8', 80))  # Using Google's DNS server
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = 'Unable to get IP address'
    finally:
        s.close()
    return ip_address

def get_options() -> RGBMatrixOptions:
    """
    Returns the RGBMatrixOptions object based on the platform.

    Returns:
        RGBMatrixOptions: RGBMatrixOptions object
    """
    options = RGBMatrixOptions()

    if platform.system() == 'Windows':
        options.rows = int(256)
        options.cols = int(384)
    else:
        options.cols = 128
        options.rows = 64
        options.pixel_mapper_config = 'V-mapper'
        options.chain_length = 4
        options.parallel = 3
        options.disable_hardware_pulsing = True
        options.pwm_bits = 1
        options.gpio_slowdown = 4

    return options

class Scoreboard:
    """
    This class is used to manage the scoreboard

    Raises:
        ValueError: If an invalid mode is passed
    """
    _acceptable_modes = ('basic', 'dual', 'detailed', 'gamecast')
    def __init__(self, games: List[dict], mode: str = 'detailed'):
        self.games: List[dict] = games
        self.mode: str = mode
        self._new_mode: str = mode

        self._welcome_message_given: bool = False

        self.display_manager = DisplayManager(get_options())

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
            if self.all_games.count_games() == 0:
                if self._welcome_message_given is False:
                    self.print_welcome_message()
            else:
                self._welcome_message_given = False

            if self.mode == 'gamecast':
                self.gamecast.print_gamecast()

            self.all_games.loop(self.mode)

            if self.mode != self.new_mode:
                self.mode = self.new_mode
                self.display_manager.clear_section(0, 0, 384, 256)

    def print_welcome_message(self):
        """
        This method is used to print the welcome message on the scoreboard
        Includes the IP address of the scoreboard
        """
        self._welcome_message_given = True
        font = Fonts.ter_u18b
        white = Colors.white
        green = Colors.green

        self.display_manager.draw_text(font, 0, 15, white, 'onDeck')

        # print ip address
        ip_address = get_ip_address()
        self.display_manager.draw_text(font, 0, 30, green, ip_address)
        self.display_manager.swap_frame()
