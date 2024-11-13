import platform

if platform.system() == 'Windows':
    from RGBMatrixEmulator import graphics # pylint: disable=E0401
else:
    from rgbmatrix import graphics # pylint: disable=E0401

class Colors:
    """
    This class is used to store the colors used in the scoreboard.
    """
    black = graphics.Color(0, 0, 0)
    white = graphics.Color(255, 255, 255)

    red = graphics.Color(255, 0, 0)
    green = graphics.Color(0, 255, 0)
    blue = graphics.Color(0, 0, 255)

    yellow = graphics.Color(255, 255, 0)
    magenta = graphics.Color(255, 0, 255)
    light_blue = graphics.Color(0, 255, 255)

    x = graphics.Color(0, 64, 255)

    # These colors require pwm_bits >= 2
    orange = graphics.Color(255, 170, 0)

    # wont show on display due to pwm bits
    grey = graphics.Color(20, 20, 20)