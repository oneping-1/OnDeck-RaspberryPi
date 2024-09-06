"""
This module is used to create a scoreboard server. Used to recieve data
from the game and display it on the scoreboard. The scoreboard can be
displayed in different modes: basic, detailed, dual, and gamecast.
"""
from typing import List, Union
import os
import threading
import platform
import math
import time
import copy
from flask import Flask, request, jsonify

if platform.system() == 'Windows':
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics # pylint: disable=E0401
else:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics # pylint: disable=E0401

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
        options.gpio_slowdown = 5

    return options

def recursive_update(d: dict, u: dict) -> dict:
    """
    Recursively updates a dictionary.

    Args:
        d (dict): Dictionary 1
        u (dict): Dictionary 2

    Returns:
        dict: Updated dictionary
    """
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

class MainServer:
    """
    This class is used to create a scoreboard server. Used to recieve
    data from the game and display it on the scoreboard.
    """
    def __init__(self, games: List[dict], scoreboard: 'Scoreboard'):
        self.games = games
        self.scoreboard = scoreboard

        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'home', self.home, methods=['GET'])
        self.app.add_url_rule('/reset', 'reset_games', self.reset_games, methods=['GET'])
        self.app.add_url_rule('/settings', 'settings', self.settings, methods=['GET'])
        self.app.add_url_rule('/<int:game_index>', 'receive_data',
            self.receive_data, methods=['POST'])
        self.app.add_url_rule('/gamecast', 'gamecast', self.gamecast, methods=['POST'])

    def home(self):
        """
        Description: This function is the home page of the scoreboard.
        Used to make sure the server is running.
        """
        d = []

        for game in self.games:
            d.append(game)

        return jsonify(d), 200

    def reset_games(self):
        """
        Description: This function is used to reset all the games.
        """
        for game in self.games:
            game['display_game'] = False

        # self.scoreboard.gamecast_game['display_game'] = False
        self.scoreboard.gamecast.gamecast_game['display_game'] = False

        for i in range(10):
            self.scoreboard.all_games.clear_game(i)

        # self.scoreboard.matrix.SwapOnVSync(self.scoreboard.canvas)
        self.scoreboard.display_manager.swap_frame()

        return jsonify({'message': 'Games reset'}), 200

    def settings(self):
        """
        Description: This function is used to set the mode of the scoreboard.
        """
        mode = request.args.get('mode')
        gameid = request.args.get('id')

        return_dict = {
            'mode': self.scoreboard.mode,
            'new_mode': self.scoreboard.new_mode
        }

        if mode is None and gameid is None:
            return jsonify({'message': return_dict}), 200

        try:
            self.scoreboard.new_mode = mode
        except ValueError:
            return jsonify({'message': f'Mode {mode} not recognized'}), 200

        if gameid is not None:
            try:
                self.scoreboard.gamecast.game_id = int(gameid)
            except ValueError:
                return jsonify({'message': 'Game ID not recognized'}), 200

        return_dict = {
            'mode': self.scoreboard.mode,
            'new_mode': self.scoreboard.new_mode
        }

        return jsonify({'message': return_dict}), 200

    def receive_data(self, game_index: int):
        """
        Description: This function is used to receive data from the game.
        The data is in the form of a JSON object.
        """
        new_data = request.get_json()

        self.games[game_index] = recursive_update(self.games[game_index], new_data)
        self.games[game_index]['display_game'] = True

        return_dict = {'new_data': new_data, 'game': self.games[game_index]}

        self.print_game_if_on_page(game_index)

        # print(json.dumps(return_dict, indent=4))
        return jsonify(return_dict), 200

    def gamecast(self):
        """
        Description: This function is used to receive data from the gamecast.
        The data is in the form of a JSON object.
        """

        new_data = request.get_json()

        r = recursive_update(self.scoreboard.gamecast.gamecast_game, new_data)
        self.scoreboard.gamecast.gamecast_game = r
        self.scoreboard.gamecast.gamecast_game['display_game'] = True

        if self.scoreboard.mode == 'gamecast':
            self.scoreboard.gamecast.print_gamecast()

        return_data = {'new_data': new_data, 'game': self.scoreboard.gamecast.gamecast_game}
        return jsonify(return_data), 200

    def print_game_if_on_page(self, game_index: int) -> bool:
        """
        This function is used to print the game if it is on the current page.

        Args:
            game_index (int): The index of the game to print.
        """
        games_per_page = 5
        shifted_game_index = game_index - (self.scoreboard.all_games.page * games_per_page)

        if self.scoreboard.mode in ('basic', 'detailed', 'gamecast'):
            if shifted_game_index > 4:
                return False

        if self.scoreboard.mode == 'dual':
            if shifted_game_index > 9:
                return False

        self.scoreboard.all_games.print_game(shifted_game_index, self.games[game_index])
        self.scoreboard.display_manager.swap_frame()
        return True

    def start(self, port: int = 5000, debug: bool = False):
        """
        Starts the Flask server

        Args:
            port (int, optional): Flask server port. Defaults to 5000.
            debug (bool, optional): Debug mode. Defaults to False.
        """
        self.app.run(host='0.0.0.0', port=port, debug=debug)

class Colors:
    """
    This class is used to store the colors used in the scoreboard.
    """
    def __init__(self):
        self.white = graphics.Color(255, 255, 255)
        self.red = graphics.Color(255, 0, 0)
        self.green = graphics.Color(0, 255, 0)
        self.blue = graphics.Color(0, 0, 255)
        self.grey = graphics.Color(20, 20, 20)
        self.black = graphics.Color(0, 0, 0)

class Fonts:
    """
    This class is used to store the fonts used in the scoreboard.
    """
    def __init__(self):
        scoreboard_path = os.path.dirname(os.path.abspath(__file__))
        fonts_path = os.path.join(scoreboard_path, 'fonts')
        terminus_path = os.path.join(fonts_path, 'Terminus')

        self.ter_u32b = graphics.Font()
        self.ter_u32b.LoadFont(os.path.join(terminus_path, 'ter-u32b.bdf'))
        # ter-u32b.bdf:
        # Letter height = 20 pixels = 38 mm = 1.496 in
        # Slighly larger than OnDeck1 (36 mm)

        self.ter_u18b = graphics.Font()
        self.ter_u18b.LoadFont(os.path.join(terminus_path, 'ter-u18b.bdf'))

        self.symbols = graphics.Font()
        self.symbols.LoadFont(os.path.join(fonts_path, 'symbols.bdf'))

class DisplayManager:
    """
    This class is used to manage the display of the scoreboard.
    """
    def __init__(self):
        self.options = get_options()
        self.matrix = RGBMatrix(options=self.options)
        self.canvas = self.matrix.CreateFrameCanvas()

        self.colors = Colors()
        self.fonts = Fonts()

        if platform.system() == 'Windows':
            # Fill the screen with grey so that the pixels can be seen
            # on the emulated display
            self.matrix.Fill(20, 20, 20)

    def swap_frame(self):
        """This method is used to swap the frame on the display."""
        self.matrix.SwapOnVSync(self.canvas)

    def draw_text(self, font: graphics.Font, x: int, y: int,
        color: graphics.Color, text: str):
        """This method is used to draw text on the display."""
        graphics.DrawText(self.canvas, font, x, y, color, text)

    def clear_section(self, x1, y1, x2, y2):
        """This method is used to clear a section of the display."""
        num_rows = y2 - y1 + 1

        if platform.system() == 'Windows':
            color = self.colors.grey
        else:
            color = self.colors.black

        for i in range(num_rows):
            graphics.DrawLine(self.canvas, x1, y1 + i, x2, y1 + i, color)

class AllGames:
    """
    This class is used to manage all the games on the scoreboard
    """
    def __init__(self, display_manager: DisplayManager, games: List[dict], mode: str = 'basic'):
        self.display_manager = display_manager
        self.games = games

        self.mode: str = None

        self.ter_u32b = self.display_manager.fonts.ter_u32b
        self.ter_u18b = self.display_manager.fonts.ter_u18b
        self.symbols = self.display_manager.fonts.symbols

        self._new_mode: str = mode
        self.num_pages: int = None

        self.page: int = 0

        # Scoreboard Offsets
        self.away_row_offset = 22
        self.home_row_offset = 44
        self.inning_row_offset = (self.away_row_offset + self.home_row_offset) / 2
        self.inning_column_offset = 100
        self.time_offset = -25

        # Detail Mode Offsets
        self.two_line_offset = 7

        self._gamecast_color = self.display_manager.colors.white

    def _print_line_a(self, color, column_offset, row_offset, line_a):
        graphics.DrawText(self.display_manager.canvas, self.ter_u18b,
            175 + column_offset, 14 + row_offset, color, line_a)

    def _print_line_b(self, color, column_offset, row_offset, line_b):
        graphics.DrawText(self.display_manager.canvas, self.ter_u18b,
            175 + column_offset, 29 + row_offset, color, line_b)

    def _print_line_c(self, color, column_offset, row_offset, line_c):
        graphics.DrawText(self.display_manager.canvas, self.ter_u18b,
            175 + column_offset, 44 + row_offset, color, line_c)

    def _calculate_offsets(self, index: int):
        row_offset = 50*index
        column_offset = 0

        if index >= 5:
            column_offset = 384/2
            row_offset = 50*(index - 5)

        return (row_offset, column_offset)

    def _calculate_color(self, index: int):
        if index % 2 == 0:
            return self.display_manager.colors.white
        return self.display_manager.colors.green

    def clear_game(self, index: int):
        """
        Clears the game from the scoreboard

        Args:
            index (int): The index of the game to clear
        """
        row_offset, column_offset = self._calculate_offsets(index)

        if self.mode in ('basic', 'dual', 'gamecast'):
            length = 192
        elif self.mode == 'detailed':
            length = 384
        else:
            raise ValueError(f'Length not specified for mode: {self.mode}')

        x1 = 0 + column_offset
        y1 = 0 + row_offset
        x2 = length + column_offset
        y2 = 50 + row_offset

        self.display_manager.clear_section(x1, y1, x2, y2)

    def _print_scores(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        if game['away_score'] > 9:
            graphics.DrawText(self.display_manager.canvas, self.ter_u32b,
                55 + column_offset, self.away_row_offset + row_offset, color,
                str(game['away_score']))
        else:
            graphics.DrawText(self.display_manager.canvas, self.ter_u32b,
                63 + column_offset, self.away_row_offset + row_offset, color,
                str(game['away_score']))

        if game['home_score'] > 9:
            graphics.DrawText(self.display_manager.canvas, self.ter_u32b,
                55 + column_offset, self.home_row_offset + row_offset, color,
                str(game['home_score']))
        else:
            graphics.DrawText(self.display_manager.canvas, self.ter_u32b,
                63 + column_offset, self.home_row_offset + row_offset, color,
                str(game['home_score']))

    def _print_inning(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        if game['inning'] > 9:
            graphics.DrawText(self.display_manager.canvas, self.ter_u32b,
                self.inning_column_offset - 8 + column_offset,
                self.inning_row_offset + row_offset, color, f'{game["inning"]}')
        else:
            graphics.DrawText(self.display_manager.canvas, self.ter_u32b,
                self.inning_column_offset + column_offset,
                self.inning_row_offset + row_offset, color, f'{game["inning"]}')

        if game['inning_state'] == 'T':
            graphics.DrawText(self.display_manager.canvas, self.symbols,
                self.inning_column_offset + column_offset,
                11 + row_offset, color, '^')
        elif game['inning_state'] == 'B':
            graphics.DrawText(self.display_manager.canvas, self.symbols,
                self.inning_column_offset + column_offset,
                43 + row_offset, color, 'v')

    def _print_text(self, index: int, text: str, column_offset: int = 0):
        row_offset, column_offset2 = self._calculate_offsets(index)
        color = self._calculate_color(index)

        x = self.inning_column_offset + column_offset + column_offset2
        y = self.inning_row_offset + row_offset
        graphics.DrawText(self.display_manager.canvas, self.ter_u32b, x, y, color, text)

    def _print_outs(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        outs_list = ['o', 'o', 'o']

        if game['count']['outs'] is None:
            pass
        else:
            if game['count']['outs'] > 0:
                outs_list[0] = 'O'
            if game['count']['outs'] > 1:
                outs_list[1] = 'O'
            if game['count']['outs'] > 2:
                outs_list[2] = 'O'

        graphics.DrawText(self.display_manager.canvas, self.symbols,
            130 + column_offset, 43 + row_offset, color, outs_list[0])
        graphics.DrawText(self.display_manager.canvas, self.symbols,
            142 + column_offset, 43 + row_offset, color, outs_list[1])
        graphics.DrawText(self.display_manager.canvas, self.symbols,
            154 + column_offset, 43 + row_offset, color, outs_list[2])

    def _print_runners(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        second_base_column_offset = 137
        second_base_row_offset = 22
        base_length = 9
        base_gap = 2
        base_offset = base_length + base_gap

        bases_list = ['b', 'b', 'b']
        if game['runners'] & 1:
            bases_list[0] = 'B'
        if game['runners'] & 2:
            bases_list[1] = 'B'
        if game['runners'] & 4:
            bases_list[2] = 'B'

        x0 = second_base_column_offset + base_offset + column_offset
        y0 = second_base_row_offset + base_offset + row_offset
        graphics.DrawText(self.display_manager.canvas, self.symbols, x0, y0,
            color, bases_list[0])

        x1 = second_base_column_offset + column_offset
        y1 = second_base_row_offset + row_offset
        graphics.DrawText(self.display_manager.canvas, self.symbols, x1, y1,
            color, bases_list[1])

        x2 = second_base_column_offset - base_offset + column_offset
        y2 = second_base_row_offset + base_offset + row_offset
        graphics.DrawText(self.display_manager.canvas, self.symbols, x2, y2,
            color, bases_list[2])

    def _print_batter_pitcher(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        line_a = None
        line_c = None

        is_top_inning = True if game['inning_state'] == 'T' else False

        if game['count']['outs'] == 3:
            # After the 3rd out is recorded, the data shows the
            # next half inning's batter and pitcher
            is_top_inning = not is_top_inning

        if is_top_inning is True:
            line_a = f'B:{game["matchup"]["batter"]} ({game["matchup"]["batter_summary"]})'
            line_c = f'P:{game["matchup"]["pitcher"]} ({game["matchup"]["pitcher_summary"]})'

        elif is_top_inning is False:
            line_a = f'P:{game["matchup"]["pitcher"]} ({game["matchup"]["pitcher_summary"]})'
            line_c = f'B:{game["matchup"]["batter"]} ({game["matchup"]["batter_summary"]})'

        if line_a is not None:
            self._print_line_a(color, column_offset, row_offset + self.two_line_offset, line_a)

        if line_c is not None:
            self._print_line_c(color, column_offset, row_offset - self.two_line_offset, line_c)

    def _print_pitcher_decisions(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        away_score = game['away_score']
        home_score = game['home_score']

        win = game['decisions']['win']
        loss = game['decisions']['loss']
        save = game['decisions']['save']

        win_summary = game['decisions']['win_summary']
        loss_summary = game['decisions']['loss_summary']
        save_summary = game['decisions']['save_summary']

        line_a = None
        line_b = None
        line_c = None

        if away_score > home_score:
            line_a = f'WP:{win} ({win_summary})'
            line_c = f'LP:{loss} ({loss_summary})'

            if save is not None:
                line_b = f'SV:{save} ({save_summary})'

        elif home_score > away_score:
            line_a = f'LP:{loss} ({loss_summary})'
            line_c = f'WP:{win} ({win_summary})'

            if save is not None:
                line_b = f'SV:{save} ({save_summary})'

        if line_b is not None:
            delta_y = 0
        else:
            delta_y = self.two_line_offset

        if line_a is not None:
            self._print_line_a(color, column_offset, row_offset + delta_y, line_a)

        if line_b is not None:
            self._print_line_b(color, column_offset, row_offset, line_b)

        if line_c is not None:
            self._print_line_c(color, column_offset, row_offset - delta_y, line_c)

    def _print_probable_pitchers(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        line_a = f'SP:{game["probables"]["away"]} ({game["probables"]["away_era"]})'
        line_c = f'SP:{game["probables"]["home"]} ({game["probables"]["home_era"]})'

        if line_a is not None:
            self._print_line_a(color, column_offset, row_offset + self.two_line_offset, line_a)

        if line_c is not None:
            self._print_line_c(color, column_offset, row_offset - self.two_line_offset, line_c)

    def _print_page_indicator(self, page_num: int):
        graphics.DrawLine(self.display_manager.canvas, 0, 255, 384, 255,
            self.display_manager.colors.black)

        line_length = 5
        gap = 2
        total_length = line_length + gap

        for i in range(page_num+1):
            x0 = 40 + ((i + 1) * total_length)
            x1 = x0 + line_length - 1 # -1 to account for extra character width

            graphics.DrawLine(self.display_manager.canvas, x0, 255, x1, 255,
                self.display_manager.colors.white)

    def print_game(self, game_index: int, game: dict):
        """
        Description: This function is used to print a game on the scoreboard.

        Args:
            game_index (int): The index of the game to print
            game (dict): The game data to print
        """
        self.clear_game(game_index)

        if game['display_game'] is False:
            return

        row_offset, column_offset = self._calculate_offsets(game_index)

        color = self._calculate_color(game_index)

        # Team Abbreviations

        graphics.DrawText(self.display_manager.canvas, self.ter_u32b,
            0 + column_offset, self.away_row_offset + row_offset, color,
            game['away']['abv'])

        graphics.DrawText(self.display_manager.canvas, self.ter_u32b,
            0 + column_offset, self.home_row_offset + row_offset, color,
            game['home']['abv'])

        # Live
        if game['game_state'] == 'L':
            self._print_scores(game_index, game)
            self._print_inning(game_index, game)
            self._print_outs(game_index, game)
            self._print_runners(game_index, game)

        # Final
        elif game['game_state'] == 'F':
            self._print_scores(game_index, game)

            if game['inning'] != 9:
                self._print_text(game_index, f'F/{game["inning"]}')
            else:
                self._print_text(game_index, 'F')

        # Pre-Game
        elif game['game_state'] == 'P':
            if len(game['start_time']) > 4:
                # -16 to account for extra character width
                self._print_text(game_index, game['start_time'], self.time_offset - 6)
            else:
                self._print_text(game_index, game['start_time'], self.time_offset + 10)

        # Suspendend / Postponed
        elif game['game_state'] == 'S':
            self._print_scores(game_index, game)
            self._print_inning(game_index, game)

            if self.mode in ('basic', 'gamecast'):
                self._print_text(game_index, 'Susp', 25)

        # Delay
        elif game['game_state'] == 'D':
            self._print_scores(game_index, game)
            self._print_inning(game_index, game)

            if self.mode in ('basic', 'gamecast'):
                self._print_text(game_index, 'Dly', 32)

        # Detailed (2 Columns)
        if self.mode != 'detailed':
            return

        # Live
        if game['game_state'] == 'L':
            self._print_batter_pitcher(game_index, game)

        # Final
        elif game['game_state'] == 'F':
            self._print_pitcher_decisions(game_index, game)

        # Pre-Game
        elif game['game_state'] == 'P':
            self._print_probable_pitchers(game_index, game)

        # Suspendend / Postponed
        elif game['game_state'] == 'S':
            self._print_text(game_index, 'Suspended', 75)
            self._print_inning(game_index, game)
            self._print_runners(game_index, game)
            self._print_outs(game_index, game)

        # Delay
        elif game['game_state'] == 'D':
            self._print_text(game_index, 'Delayed', 75)
            self._print_inning(game_index, game)
            self._print_runners(game_index, game)
            self._print_outs(game_index, game)

    def print_page(self, page_num: int):
        """
        This method is used to print a page of games on the scoreboard.

        Args:
            page_num (int): The page number to print
        """
        max_games = 5 * self.num_pages
        shift_offset = page_num * 5

        shifted_games = [None] * max_games

        for i, game in enumerate(self.games[:max_games]):
            shifted_games[i] = game

        shifted_games = shifted_games[shift_offset:] + shifted_games[:shift_offset]

        if self.mode == 'dual':
            shifted_games = shifted_games[:10]
        else:
            shifted_games = shifted_games[:5]

        for i, game in enumerate(shifted_games):
            self.print_game(i, game)

        self._print_page_indicator(page_num)

        self.display_manager.swap_frame()
        time.sleep(10)

    def _count_games(self) -> int:
        count = 0

        for game in self.games:
            if game['display_game'] is True:
                count += 1

        return count

    def loop(self, mode: str):
        """
        This method is used to loop through the games on the scoreboard.

        Args:
            mode (str): The mode of the scoreboard
        """
        self.mode = mode
        self.num_pages = math.ceil(self._count_games() / 5)

        a = (self.num_pages <= 2) and (mode == 'dual')
        b = (self.num_pages <= 1) and (mode == 'basic')
        cycle_pages = not (a or b)

        if not cycle_pages:
            # No need to loop, all games fit. would just alternate
            # the one or two columns
            return

        for self.page in range(self.num_pages):
            self.print_page(self.page)

class Gamecast:
    """
    This class is used to manage the gamecast on the scoreboard
    """
    def __init__(self, display_manager: DisplayManager, games: List[dict], game_id: int = -1):
        self.display_manager = display_manager
        self.games = games
        self.game_id = game_id
        self.gamecast_game = copy.deepcopy(games[game_id])

        self._gamecast_color = self.display_manager.colors.white

        self.ter_u18b = self.display_manager.fonts.ter_u18b
        self.symbols = self.display_manager.fonts.symbols

    def _clear_gamecast(self):
        self.display_manager.clear_section(192, 0, 384, 256)

    def _print_gamecast_line(self, line_num: int, text: Union[str, None]) -> bool:
        if text is None:
            return False

        row = 16 * (line_num + 1)

        self.display_manager.draw_text(self.ter_u18b, 192, row, self._gamecast_color, text)
        return True

    def _print_gamecast_inning_arrows(self):
        if self.gamecast_game['inning_state'] == 'T':
            self.display_manager.draw_text(self.symbols, 320, 8, self._gamecast_color, '_')
        elif self.gamecast_game['inning_state'] == 'B':
            self.display_manager.draw_text(self.symbols, 320, 29, self._gamecast_color, 'w')

    def _print_gamecast_bases(self):
        second_base_column_offset = 347
        second_base_row_offset = 15
        base_length = 5
        base_gap = 2
        base_offset = base_length + base_gap

        bases_list = ['c', 'c', 'c']
        if self.gamecast_game['runners'] & 1:
            bases_list[0] = 'C'
        if self.gamecast_game['runners'] & 2:
            bases_list[1] = 'C'
        if self.gamecast_game['runners'] & 4:
            bases_list[2] = 'C'

        x0 = second_base_column_offset + base_offset
        y0 = second_base_row_offset + base_offset
        self.display_manager.draw_text(self.symbols, x0, y0, self._gamecast_color, bases_list[0])

        x1 = second_base_column_offset
        y1 = second_base_row_offset
        self.display_manager.draw_text(self.symbols, x1, y1, self._gamecast_color, bases_list[1])

        x2 = second_base_column_offset - base_offset
        y2 = second_base_row_offset + base_offset
        self.display_manager.draw_text(self.symbols, x2, y2, self._gamecast_color, bases_list[2])

    def _print_gamecast_outs(self):
        outs_list = ['p', 'p', 'p']

        if self.gamecast_game['count']['outs'] is None:
            pass
        else:
            if self.gamecast_game['count']['outs'] > 0:
                outs_list[0] = 'P'
            if self.gamecast_game['count']['outs'] > 1:
                outs_list[1] = 'P'
            if self.gamecast_game['count']['outs'] > 2:
                outs_list[2] = 'P'

        self.display_manager.draw_text(self.symbols, 344, 28, self._gamecast_color, outs_list[0])
        self.display_manager.draw_text(self.symbols, 350, 28, self._gamecast_color, outs_list[1])
        self.display_manager.draw_text(self.symbols, 356, 28, self._gamecast_color, outs_list[2])

    def _print_gamecast_count(self):
        count = f'{self.gamecast_game["count"]["balls"]}-{self.gamecast_game["count"]["strikes"]}'
        count += f' {self.gamecast_game["count"]["outs"]} Out'
        if self.gamecast_game['count']['outs'] != 1:
            count += 's'
        self._print_gamecast_line(2, count)

    def _print_gamecast_umpire_details(self) -> bool:
        game = self.gamecast_game

        if game['umpire']['num_missed'] is None:
            return False

        if game['umpire']['home_favor'] < 0:
            abv = game['away']['abv']
            favor = -1 * game['umpire']['home_favor']
        else:
            abv = game['home']['abv']
            favor = game['umpire']['home_favor']

        s = f'Ump: +{favor:.2f} {abv} ({game["umpire"]["num_missed"]})'
        self._print_gamecast_line(4, s)

        return True

    def _print_gamecast_run_expectancy_details(self) -> bool:
        game = self.gamecast_game

        if game['run_expectancy']['average_runs'] is None:
            return False

        self._print_gamecast_line(5, f'Avg Runs: {game["run_expectancy"]["average_runs"]:.2f}')
        return True

    def _print_gamecast_win_probability_details(self):
        game = self.gamecast_game

        if game['win_probability']['away'] is None:
            return False

        away_win = game['win_probability']['away'] * 100
        home_win = game['win_probability']['home'] * 100

        if away_win > home_win:
            win = away_win
            abv = game['away']['abv']
        else:
            win = home_win
            abv = game['home']['abv']

        s = f'Win Prob: {win:.1f}% {abv}'
        self._print_gamecast_line(6, s)

        return True

    def _print_gamecast_pitch_details(self):
        self._print_gamecast_line(8, self.gamecast_game['pitch_details']['description'])

        s = ''
        if self.gamecast_game['pitch_details']['speed'] is not None:
            # Both are either a value or None
            # None on no pitch like step off
            s += f'{self.gamecast_game["pitch_details"]["speed"]} MPH'
            s += f'  Zone:{self.gamecast_game["pitch_details"]["zone"]:>2d}'
        self._print_gamecast_line(9, s)

        self._print_gamecast_line(10, self.gamecast_game['pitch_details']['type'])

    def _print_gamecast_hit_details(self) -> bool:
        game = self.gamecast_game

        if game['hit_details']['distance'] is None:
            # Check for one of the hit details
            return False

        self._print_gamecast_line(12, f'Dist: {game["hit_details"]["distance"]:>5.1f} ft')
        self._print_gamecast_line(13, f'  EV: {game["hit_details"]["exit_velo"]:>5.1f} MPH')
        self._print_gamecast_line(14, f'  LA: {game["hit_details"]["launch_angle"]:>5.1f}°')
        count = f'{self.gamecast_game["count"]["balls"]}-{self.gamecast_game["count"]["strikes"]}'
        count += f' {self.gamecast_game["count"]["outs"]} Out'
        if self.gamecast_game['count']['outs'] != 1:
            count += 's'

        return True

    def print_gamecast(self) -> bool:
        """
        This method is used to print the gamecast on the scoreboard.
        """
        self._clear_gamecast()

        if self.gamecast_game['display_game'] is False:
            return False

        away_row_offset = 14
        home_row_offset = 30
        inning_row_offset = (away_row_offset + home_row_offset) / 2

        self._print_gamecast_line(0, self.gamecast_game['away']['name'])
        self._print_gamecast_line(1, self.gamecast_game['home']['name'])

        # Scores
        self.display_manager.draw_text(self.ter_u18b, 300, away_row_offset,
            self._gamecast_color, str(self.gamecast_game['away_score']))

        self.display_manager.draw_text(self.ter_u18b, 300, home_row_offset,
            self._gamecast_color, str(self.gamecast_game['home_score']))

        # Inning
        self.display_manager.draw_text(self.ter_u18b, 320, inning_row_offset,
            self._gamecast_color, str(self.gamecast_game['inning']))

        self._print_gamecast_inning_arrows()
        self._print_gamecast_bases()
        self._print_gamecast_outs()
        self._print_gamecast_count()
        self._print_gamecast_umpire_details()
        self._print_gamecast_run_expectancy_details()
        self._print_gamecast_win_probability_details()
        self._print_gamecast_pitch_details()
        self._print_gamecast_hit_details()

        self.display_manager.swap_frame()
        return True

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

def start_server(server):
    """Starts the server"""
    server.start()

def start_scoreboard(scoreboard):
    """Starts the scoreboard"""
    scoreboard.start()

def main():
    """
    Description: This function is used to start the scoreboard
    """
    game_template = {
        'game_state': None,
        'away_score': None,
        'home_score': None,
        'inning': None,
        'inning_state': None,
        'away': {
            'abv': None,
            'name': None,
            'location': None,
        },
        'home': {
            'abv': None,
            'name': None,
            'location': None
        },
        'count': {
            'balls': None,
            'strikes': None,
            'outs': None
        },
        'runners': None,
        'start_time': None,
        'matchup': {
            'batter': None,
            'batter_summary': None,
            'pitcher': None,
            'pitcher_summary': None
        },
        'decisions': {
            'win': None,
            'win_summary': None,
            'loss': None,
            'loss_summary': None,
            'save': None,
            'save_summary': None
        },
        'probables': {
            'away': None,
            'away_era': None,
            'home': None,
            'home_era': None
        },
        'pitch_details': {
            'description': None,
            'speed': None,
            'type': None,
            'zone': None,
            'spin_rate': None,
        },
        'hit_details': {
            'distance': None,
            'exit_velo': None,
            'launch_angle': None
        },
        'umpire': {
            'num_missed': None,
            'home_favor': None,
            'home_wpa': None
        },
        'run_expectancy': {
            'average_runs': None
        },
        'win_probability':{
            'away': None,
            'home': None,
            'extras': None
        },
        'display_game': False
    }

    games = [copy.deepcopy(game_template) for _ in range(20)]

    scoreboard = Scoreboard(games)
    main_server = MainServer(games, scoreboard)

    server_thread = threading.Thread(target=start_server, args=(main_server,))
    scoreboard_thread = threading.Thread(target=start_scoreboard, args=(scoreboard,))

    server_thread.start()
    scoreboard_thread.start()

if __name__ == '__main__':
    main()