from typing import List
import json
import threading
import platform
import math
import time
from flask import Flask, request, jsonify

if platform.system() == 'Windows':
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
else:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

def get_options() -> RGBMatrixOptions:
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

        options.pwm_bits = 7
        # dither?

    return options

class Server:
    """
    Description: This class is used to create a scoreboard server.
    Used to recieve data from the game and display it on the scoreboard.
    """
    def __init__(self, games: List[dict]):
        self.games = games

        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'home', self.home, methods=['GET'])
        self.app.add_url_rule('/<int:game_index>', 'receive_data',
            self.receive_data, methods=['POST'])

    def home(self):
        """
        Description: This function is the home page of the scoreboard.
        Used to make sure the server is running.
        """
        d = []

        for game in self.games:
            d.append(game)

        return jsonify(d), 200

    def receive_data(self, game_index: int):
        """
        Description: This function is used to receive data from the game.
        The data is in the form of a JSON object.
        """
        new_data = request.get_json()

        for key, value in new_data.items():
            self.games[game_index][key] = value
        self.games[game_index]['display_game'] = True

        return_dict = {'new_data': new_data, 'game': self.games[game_index]}

        # print(json.dumps(return_dict, indent=4))
        return jsonify(return_dict), 200

    def start(self, port: int = 5000, debug: bool = False):
        """
        Starts the Flask server

        Args:
            port (int, optional): Flask server port. Defaults to 5000.
            debug (bool, optional): Debug mode. Defaults to False.
        """
        self.app.run(host='0.0.0.0', port=port, debug=debug)

class Scoreboard:
    """
    Description: This class is used to create a scoreboard.
    Used to display the data from the game on the scoreboard.
    """
    def __init__(self, games: List[dict]):
        self.games = games
        self.mode: str = 'basic'
        self.num_pages: int = None

        # Matrix Setup
        self.options = get_options()
        self.matrix = RGBMatrix(options=self.options)
        self.canvas = self.matrix.CreateFrameCanvas()

        self.ter_u32b = graphics.Font()
        self.ter_u32b.LoadFont('fonts/Terminus/ter-u32b.bdf')
        # ter-u32b.bdf:
        # Letter height = 20 pixels = 38 mm = 1.496 in
        # Slighly larger than OnDeck1 (36 mm)

        self.ter = graphics.Font()
        self.ter.LoadFont('fonts/Terminus/ter-u18b.bdf')

        self.symbols = graphics.Font()
        self.symbols.LoadFont('fonts/symbols.bdf')

        # Matrix Colors
        self.my_white = graphics.Color(255, 255, 255)
        self.my_red = graphics.Color(255, 0, 0)
        self.my_green = graphics.Color(0, 255, 0)
        self.my_blue = graphics.Color(0, 0, 255)
        self.my_grey = graphics.Color(20, 20, 20)
        self.my_black = graphics.Color(0, 0, 0)

        if platform.system() == 'Windows':
            # Fill the screen with grey
            # Can see pixels in emulation
            self.matrix.Fill(20, 20, 20)

        # Scoreboard Offsets
        self.away_row_offset = 22
        self.home_row_offset = 44
        self.inning_row_offset = (self.away_row_offset + self.home_row_offset) / 2
        self.inning_column_offset = 100
        self.time_offset = -25

    def _calculate_offsets(self, index: int):
        row_offset = 50*index
        column_offset = 0

        if index >= 5:
            column_offset = 384/2
            row_offset = 50*(index - 5)

        return (row_offset, column_offset)

    def _calculate_color(self, index: int):
        if index % 2 == 0:
            return self.my_white
        return self.my_green

    def _clear_game(self, index: int):
        row_offset, column_offset = self._calculate_offsets(index)

        if platform.system() == 'Windows':
            color = self.my_grey
        else:
            color = self.my_black

        if self.mode == 'basic':
            length = 192
        elif self.mode == 'detailed':
            length = 384

        for i in range(50):
            graphics.DrawLine(self.canvas, 0 + column_offset, i + row_offset,
                length + column_offset, i + row_offset, color)

    def _print_scores(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        if game['away_score'] > 9:
            graphics.DrawText(self.canvas, self.ter_u32b, 55 + column_offset,
                self.away_row_offset + row_offset, color, str(game['away_score']))
        else:
            graphics.DrawText(self.canvas, self.ter_u32b, 63 + column_offset,
                self.away_row_offset + row_offset, color, str(game['away_score']))

        if game['home_score'] > 9:
            graphics.DrawText(self.canvas, self.ter_u32b, 55 + column_offset,
                self.home_row_offset + row_offset, color, str(game['home_score']))
        else:
            graphics.DrawText(self.canvas, self.ter_u32b, 63 + column_offset,
                self.home_row_offset + row_offset, color, str(game['home_score']))

    def _print_inning(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        if game['inning'] > 9:
            graphics.DrawText(self.canvas, self.ter_u32b,  self.inning_column_offset - 8 + column_offset,
                self.inning_row_offset + row_offset, color, f'{game["inning"]}')
        else:
            graphics.DrawText(self.canvas, self.ter_u32b, self.inning_column_offset + column_offset,
                self.inning_row_offset + row_offset, color, f'{game["inning"]}')

        if game['inning_state'] == 'T':
            graphics.DrawText(self.canvas, self.symbols, self.inning_column_offset + column_offset,
                11 + row_offset, color, '^')
        elif game['inning_state'] == 'B':
            graphics.DrawText(self.canvas, self.symbols, self.inning_column_offset + column_offset,
                43 + row_offset, color, 'v')

    def _print_text(self, index: int, text: str, column_offset: int = 0):
        row_offset, column_offset2 = self._calculate_offsets(index)
        color = self._calculate_color(index)

        x = self.inning_column_offset + column_offset + column_offset2
        y = self.inning_row_offset + row_offset
        graphics.DrawText(self.canvas, self.ter_u32b, x, y, color, text)

    def _print_outs(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        outs_list = ['o', 'o', 'o']

        if game['outs'] is None:
            pass
        else:
            if game['outs'] > 0:
                outs_list[0] = 'O'
            if game['outs'] > 1:
                outs_list[1] = 'O'
            if game['outs'] > 2:
                outs_list[2] = 'O'

        graphics.DrawText(self.canvas, self.symbols, 130 + column_offset,
            43 + row_offset, color, outs_list[0])
        graphics.DrawText(self.canvas, self.symbols, 142 + column_offset,
            43 + row_offset, color, outs_list[1])
        graphics.DrawText(self.canvas, self.symbols, 154 + column_offset,
            43 + row_offset, color, outs_list[2])

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
        graphics.DrawText(self.canvas, self.symbols, x0, y0, color, bases_list[0])

        x1 = second_base_column_offset + column_offset
        y1 = second_base_row_offset + row_offset
        graphics.DrawText(self.canvas, self.symbols, x1, y1, color, bases_list[1])

        x2 = second_base_column_offset - base_offset + column_offset
        y2 = second_base_row_offset + base_offset + row_offset
        graphics.DrawText(self.canvas, self.symbols, x2, y2, color, bases_list[2])

    def _print_batter_pitcher(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        if game['inning_state'] == 'T':
            graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                14 + row_offset, color, f'B:{game["batter"]}')

            graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                44 + row_offset, color, f'P:{game["pitcher"]}')

        elif game['inning_state'] == 'B':
            graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                14 + row_offset, color, f'P:{game["pitcher"]}')

            graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                44 + row_offset, color, f'B:{game["batter"]}')

    def _print_pitcher_decisions(self, index, game):
        row_offset, column_offset = self._calculate_offsets(index)
        color = self._calculate_color(index)

        away_score = game['away_score']
        home_score = game['home_score']

        winning_pitcher = game['winning_pitcher']
        losing_pitcher = game['losing_pitcher']
        save_pitcher = game['save_pitcher']

        if away_score > home_score:
            graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                14 + row_offset, color, f'W:{winning_pitcher}')

            graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                44 + row_offset, color, f'L:{losing_pitcher}')

            if save_pitcher is not None:
                graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                    29 + row_offset, color, f'S:{save_pitcher}')

        elif home_score > away_score:
            graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                14 + row_offset, color, f'L:{losing_pitcher}')

            graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                44 + row_offset, color, f'W:{winning_pitcher}')

            if save_pitcher is not None:
                graphics.DrawText(self.canvas, self.ter, 170 + column_offset,
                    29 + row_offset, color, f'S:{save_pitcher}')

    def print_game(self, game_index: int, game: dict):
        self._clear_game(game_index)

        if game['display_game'] is False:
            return 0

        row_offset, column_offset = self._calculate_offsets(game_index)

        color = self._calculate_color(game_index)

        # Team Abbreviations
        graphics.DrawText(self.canvas, self.ter_u32b, 0 + column_offset,
            self.away_row_offset + row_offset, color, game['away_abv'])

        graphics.DrawText(self.canvas, self.ter_u32b, 0 + column_offset,
            self.home_row_offset + row_offset, color, game['home_abv'])

        if game['game_state'] == 'L':
            self._print_scores(game_index, game)
            self._print_inning(game_index, game)
            self._print_outs(game_index, game)
            self._print_runners(game_index, game)
            self._print_batter_pitcher(game_index, game)
        elif game['game_state'] == 'F':
            self._print_scores(game_index, game)
            self._print_pitcher_decisions(game_index, game)

            if game['inning'] != 9:
                self._print_text(game_index, f'F/{game["inning"]}')
            else:
                self._print_text(game_index, 'F')

        elif game['game_state'] == 'P':
            if len(game['start_time']) > 4:
                # -16 to account for extra character width
                self._print_text(game_index, game['start_time'], self.time_offset - 16)
            else:
                self._print_text(game_index, game['start_time'], self.time_offset)

        if self.mode == 'basic':
            return 0

        if game['game_state'] == 'L':
            self._print_batter_pitcher(game_index, game)
        elif game['game_state'] == 'F':
            self._print_pitcher_decisions(game_index, game)

    def print_page(self, page_num: int):
        max_games = 5 * self.num_pages
        shift_offset = page_num * 5

        shifted_games = [None] * max_games

        for i, game in enumerate(self.games[:max_games]):
            shifted_games[i] = game

        shifted_games = shifted_games[shift_offset:] + shifted_games[:shift_offset]

        if self.mode == 'basic':
            shifted_games = shifted_games[:10]
        else:
            shifted_games = shifted_games[:5]

        for i, game in enumerate(shifted_games):
            self.print_game(i, game)

        self.matrix.SwapOnVSync(self.canvas)
        time.sleep(10)

    def _count_games(self) -> int:
        count = 0

        for game in self.games:
            if game['display_game'] is True:
                count += 1

        return count

    def start(self, mode: str = 'basic'):
        self.mode = mode

        while True:
            self.num_pages = math.ceil(self._count_games() / 5)
            for page in range(self.num_pages):
                self.print_page(page)

def start_server(server):
    """Starts the server"""
    server.start()

def start_scoreboard(scoreboard):
    """Starts the scoreboard"""
    scoreboard.start(mode = 'basic')

def main():
    game_template = {
        'game_state': None,
        'away_abv': None,
        'home_abv': None,
        'away_score': None,
        'home_score': None,
        'inning': None,
        'inning_state': None,
        'balls': None,
        'strikes': None,
        'outs': None,
        'runners': None,
        'start_time': None,
        'batter': None,
        'pitcher': None,
        'winning_pitcher': None,
        'losing_pitcher': None,
        'save_pitcher': None,
        'display_game': False
    }

    games = [game_template.copy() for _ in range(20)]

    server = Server(games)
    scoreboard = Scoreboard(games)

    server_thread = threading.Thread(target=start_server, args=(server,))
    scoreboard_thread = threading.Thread(target=start_scoreboard, args=(scoreboard,))

    server_thread.start()
    scoreboard_thread.start()

if __name__ == '__main__':
    main()
