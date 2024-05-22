import curses

def setup_colors(screen):
    curses.start_color()
    if curses.can_change_color():
        # Convert RGB values from 0-255 to 0-1000
        def rgb_to_curses(r, g, b):
            return int(r * 1000 / 255), int(g * 1000 / 255), int(b * 1000 / 255)

        # Define Zernburn colors
        bg = rgb_to_curses(63, 63, 63)  # Background
        fg = rgb_to_curses(220, 220, 204)  # Foreground
        red = rgb_to_curses(112, 80, 80)  # Red
        green = rgb_to_curses(96, 180, 138)  # Green
        yellow = rgb_to_curses(223, 175, 143)  # Yellow
        blue = rgb_to_curses(80, 96, 112)  # Blue
        magenta = rgb_to_curses(220, 140, 195)  # Magenta
        cyan = rgb_to_curses(140, 208, 211)  # Cyan
        white = rgb_to_curses(220, 220, 204)  # White

        # Bold versions of the colors
        bold_red = rgb_to_curses(220, 163, 163)  # Bold Red
        bold_green = rgb_to_curses(195, 191, 159)  # Bold Green
        bold_yellow = rgb_to_curses(240, 223, 175)  # Bold Yellow
        bold_blue = rgb_to_curses(148, 191, 243)  # Bold Blue
        bold_magenta = rgb_to_curses(236, 147, 211)  # Bold Magenta
        bold_cyan = rgb_to_curses(147, 224, 227)  # Bold Cyan

        # Initialize colors
        curses.init_color(16, *bg)  # Background
        curses.init_color(17, *fg)  # Foreground
        curses.init_color(18, *red)  # Red
        curses.init_color(19, *green)  # Green
        curses.init_color(20, *yellow)  # Yellow
        curses.init_color(21, *blue)  # Blue
        curses.init_color(22, *magenta)  # Magenta
        curses.init_color(23, *cyan)  # Cyan
        curses.init_color(24, *white)  # White

        # Initialize bold colors
        curses.init_color(25, *bold_red)  # Bold Red
        curses.init_color(26, *bold_green)  # Bold Green
        curses.init_color(27, *bold_yellow)  # Bold Yellow
        curses.init_color(28, *bold_blue)  # Bold Blue
        curses.init_color(29, *bold_magenta)  # Bold Magenta
        curses.init_color(30, *bold_cyan)  # Bold Cyan

        # Define color pairs
        curses.init_pair(1, 17, 16)  # Foreground on Background
        curses.init_pair(2, 25, 16)  # Bold Red on Background (Agent color)
        curses.init_pair(3, 27, 16)  # Bold Yellow on Background (Prompt color)
        curses.init_pair(4, 19, 16)  # Green on Background
        curses.init_pair(5, 21, 16)  # Blue on Background
        curses.init_pair(6, 22, 16)  # Magenta on Background
        curses.init_pair(7, 23, 16)  # Cyan on Background
        curses.init_pair(8, 24, 16)  # White on Background
    else:
        curses.init_pair
