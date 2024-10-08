import os
import platform

if platform.system() == 'Windows':
    from RGBMatrixEmulator import graphics  # pylint: disable=E0401
else:
    from rgbmatrix import graphics  # pylint: disable=E0401

class Fonts:
    """
    This class is used to store the fonts used in the scoreboard.
    """
    f6x10 = None
    ter_u18b = None
    ter_u22b = None
    ter_u32b = None
    symbols = None

    # Class initialization block
    @classmethod
    def _initialize_fonts(cls):
        if cls.ter_u32b is None:  # Load the fonts only if they are not already loaded
            scoreboard_path = os.path.dirname(os.path.abspath(__file__))
            fonts_path = os.path.join(scoreboard_path, '..', 'fonts')
            rpi_rgb_path = os.path.join(fonts_path, 'rpi-rgb-led-matrix')
            terminus_path = os.path.join(fonts_path, 'Terminus')

            cls.f6x10 = graphics.Font()
            cls.f6x10.LoadFont(os.path.join(rpi_rgb_path, '6x10.bdf'))
            # cls.test.LoadFont(os.path.join(terminus_path, 'ter-u12b.bdf'))

            cls.ter_u18b = graphics.Font()
            cls.ter_u18b.LoadFont(os.path.join(terminus_path, 'ter-u18b.bdf'))

            cls.ter_u22b = graphics.Font()
            cls.ter_u22b.LoadFont(os.path.join(terminus_path, 'ter-u22b.bdf'))

            cls.ter_u32b = graphics.Font()
            cls.ter_u32b.LoadFont(os.path.join(terminus_path, 'ter-u32b.bdf'))

            cls.symbols = graphics.Font()
            cls.symbols.LoadFont(os.path.join(fonts_path, 'symbols.bdf'))

# Automatically run the font initialization at the time of class definition
Fonts._initialize_fonts()
