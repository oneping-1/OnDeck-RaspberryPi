
from on_deck.colors import Colors
from on_deck.fonts import Fonts
from on_deck.display_manager import DisplayManager

class Gamecast:
    def __init__(self, display_manager: DisplayManager):
        self.display_manager = display_manager
        self.game: dict = None

        self._ddo = 4 # double digit offset

    def _print_team_names(self, game: dict):
        color = Colors.white

        self.display_manager.draw_text(Fonts.ter_u16b, 128, 12, color, game['away']['name'])
        self.display_manager.draw_text(Fonts.ter_u16b, 128, 24, color, game['home']['name'])

    def _print_linescore(self, home: bool, runs: int, hits: int, errors: int, lob: int):
        color = Colors.white
        row_offset = 24 if home else 12

        run_column_offset = 80
        hit_column_offset = 100
        error_column_offset = 116
        lob_column_offset = 132

        run_column_offset -= self._ddo if runs >= 10 else 0
        hit_column_offset -= self._ddo if hits >= 10 else 0
        lob_column_offset -= self._ddo if lob >= 10 else 0

        if runs >= 10:
            self.display_manager.draw_text(Fonts.ter_u16b, 128 + run_column_offset,
                row_offset, Colors.yellow, f'{runs}')
        else:
            self.display_manager.draw_text(Fonts.ter_u16b, 128 + run_column_offset,
                row_offset, Colors.yellow, f'{runs}')

        if hits >= 10:
            self.display_manager.draw_text(Fonts.ter_u16b, 128 + hit_column_offset,
                row_offset, color, f'{hits}')
        else:
            self.display_manager.draw_text(Fonts.ter_u16b, 128 + hit_column_offset,
                row_offset, color, f'{hits}')

        self.display_manager.draw_text(Fonts.ter_u16b, 128 + error_column_offset,
            row_offset, color, f'{errors}')

        if lob >= 10:
            self.display_manager.draw_text(Fonts.ter_u16b, 128 + lob_column_offset,
                row_offset, color, f'{lob}')
        else:
            self.display_manager.draw_text(Fonts.ter_u16b, 128 + lob_column_offset,
                row_offset, color, f'{lob}')

    def _print_linescores(self, game: dict):
        runs = game['away']['runs']
        hits = game['away']['hits']
        errors = game['away']['errors']
        lob = game['away']['left_on_base']
        self._print_linescore(False, runs, hits, errors, lob)

        runs = game['home']['runs']
        hits = game['home']['hits']
        errors = game['home']['errors']
        lob = game['home']['left_on_base']
        self._print_linescore(True, runs, hits, errors, lob)

    def _print_bases(self, game: dict):
        second_base_column_offset = 128 + 160
        second_base_row_offset = 8

        base_length = 6
        base_gap = 2
        base_offset = base_length + base_gap

        thickness = 2

        bases = [False, False, False]

        if game['runners'] & 1:
            bases[0] = True
        if game['runners'] & 2:
            bases[1] = True
        if game['runners'] & 4:
            bases[2] = True

        self.display_manager.draw_diamond(second_base_column_offset - base_offset,
            second_base_row_offset + base_offset, base_length, thickness, bases[0], Colors.white)
        self.display_manager.draw_diamond(second_base_column_offset,
            second_base_row_offset, base_length, thickness, bases[1], Colors.white)
        self.display_manager.draw_diamond(second_base_column_offset + base_offset,
            second_base_row_offset + base_offset, base_length, thickness, bases[2], Colors.white)

    def _print_count(self, game: dict):
        circle_column_offset = 128 + 182
        ball_row_offset = 4
        strike_row_offset = 12
        out_row_offset = 20

        radius = 3
        gap = 1
        thickness = 1
        delta = 2*radius + gap + 1

        balls_int = game['count']['balls']
        balls = [False, False, False, False]
        if balls_int >= 1:
            balls[0] = True
        if balls_int >= 2:
            balls[1] = True
        if balls_int >= 3:
            balls[2] = True
        if balls_int >= 4:
            balls[3] = True

        self.display_manager.draw_circle(circle_column_offset + 0*delta,
            ball_row_offset, radius, thickness, balls[0], Colors.green)
        self.display_manager.draw_circle(circle_column_offset + 1*delta,
            ball_row_offset, radius, thickness, balls[1], Colors.green)
        self.display_manager.draw_circle(circle_column_offset + 2*delta,
            ball_row_offset, radius, thickness, balls[2], Colors.green)
        self.display_manager.draw_circle(circle_column_offset + 3*delta,
            ball_row_offset, radius, thickness, balls[3], Colors.green)


        strikes_int = game['count']['strikes']
        strikes = [False, False, False]
        if strikes_int >= 1:
            strikes[0] = True
        if strikes_int >= 2:
            strikes[1] = True
        if strikes_int >= 3:
            strikes[2] = True

        self.display_manager.draw_circle(circle_column_offset + 0*delta,
            strike_row_offset, radius, thickness, strikes[0], Colors.red)
        self.display_manager.draw_circle(circle_column_offset + 1*delta,
            strike_row_offset, radius, thickness, strikes[1], Colors.red)
        self.display_manager.draw_circle(circle_column_offset + 2*delta,
            strike_row_offset, radius, thickness, strikes[2], Colors.red)


        outs_int = game['count']['outs']
        outs = [False, False, False]
        if outs_int >= 1:
            outs[0] = True
        if outs_int >= 2:
            outs[1] = True
        if outs_int >= 3:
            outs[2] = True

        self.display_manager.draw_circle(circle_column_offset + 0*delta,
            out_row_offset, radius, thickness, outs[0], Colors.white)
        self.display_manager.draw_circle(circle_column_offset + 1*delta,
            out_row_offset, radius, thickness, outs[1], Colors.white)
        self.display_manager.draw_circle(circle_column_offset + 2*delta,
            out_row_offset, radius, thickness, outs[2], Colors.white)

    def print_game(self, game: dict):
        self._print_team_names(game)
        self._print_linescores(game)
        self._print_bases(game)
        self._print_count(game)
        self.display_manager.swap_frame()

if __name__ == '__main__':
    print('wrong module dummy')