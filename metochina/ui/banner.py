#!/usr/bin/env python3
"""
METOCHINA - OSINT Image Metadata Analyzer
Banner display module with multiple ASCII art styles.
"""

import os
import sys
import random
import time

# Enable Windows ANSI escape code support
os.system("")

# ──────────────────────────────────────────────
# ANSI Color Codes
# ──────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
WHITE   = "\033[97m"
GRAY    = "\033[90m"


# ──────────────────────────────────────────────
# Banner Style 1: Block / Pixel (box-drawing)
# ──────────────────────────────────────────────
BANNER_BLOCK = r"""
 ███╗   ███╗ ███████╗ ████████╗  ██████╗   ██████╗ ██╗  ██╗ ██╗ ███╗   ██╗  █████╗
 ████╗ ████║ ██╔════╝ ╚══██╔══╝ ██╔═══██╗ ██╔════╝ ██║  ██║ ██║ ████╗  ██║ ██╔══██╗
 ██╔████╔██║ █████╗      ██║    ██║   ██║ ██║      ███████║ ██║ ██╔██╗ ██║ ███████║
 ██║╚██╔╝██║ ██╔══╝      ██║    ██║   ██║ ██║      ██╔══██║ ██║ ██║╚██╗██║ ██╔══██║
 ██║ ╚═╝ ██║ ███████╗    ██║    ╚██████╔╝ ╚██████╗ ██║  ██║ ██║ ██║ ╚████║ ██║  ██║
 ╚═╝     ╚═╝ ╚══════╝    ╚═╝     ╚═════╝   ╚═════╝ ╚═╝  ╚═╝ ╚═╝ ╚═╝  ╚═══╝ ╚═╝  ╚═╝
"""

# ──────────────────────────────────────────────
# Banner Style 2: Slant / Italic
# ──────────────────────────────────────────────
BANNER_SLANT = r"""
        __  ___     __          __    _
       /  |/  /__  / /____  ___/ /_  (_)___  ___ _
      / /|_/ / _ \/ __/ _ \/ __/ _ \/ / _ \/ _ `/
     / /  / /  __/ /_/ (_) / /_/ / / / / / / /_/ /
    /_/  /_/\___/\__/\___/\__/_/ /_/_/_/ /_/\__,_/
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |  O S I N T   M E T A D A T A   T O O L |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""

# ──────────────────────────────────────────────
# Banner Style 3: Graffiti / Big
# ──────────────────────────────────────────────
BANNER_GRAFFITI = r"""
    __    __  ________  ________  ______    ______   __    __  ______  __    __   ______
   /  \  /  |/        |/        |/      \  /      \ /  |  /  |/      |/  \  /  | /      \
   $$  \ $$ |$$$$$$$$/ $$$$$$$$//$$$$$$  |/$$$$$$  |$$ |  $$ |$$$$$$/ $$  \ $$ |/$$$$$$  |
   $$$  \$$ |$$ |__       $$ |  $$ |  $$ |$$ |  $$/ $$ |__$$ |  $$ |  $$$  \$$ |$$ |__$$ |
   $$$$  $$ |$$    |      $$ |  $$ |  $$ |$$ |      $$    $$ |  $$ |  $$$$  $$ |$$    $$ |
   $$ $$ $$ |$$$$$/       $$ |  $$ |  $$ |$$ |   __ $$$$$$$$ |  $$ |  $$ $$ $$ |$$$$$$$$ |
   $$ |$$$$ |$$ |_____    $$ |  $$ \__$$ |$$ \__/  |$$ |  $$ | _$$ |_ $$ |$$$$ |$$ |  $$ |
   $$ | $$$ |$$       |   $$ |  $$    $$/ $$    $$/ $$ |  $$ |/ $$   |$$ | $$$ |$$ |  $$ |
   $$/   $$/ $$$$$$$$/    $$/    $$$$$$/   $$$$$$/  $$/   $$/ $$$$$$/ $$/   $$/ $$/   $$/
"""

# ──────────────────────────────────────────────
# Banner Style 4: Cyberpunk / Matrix
# ──────────────────────────────────────────────
BANNER_CYBER = r"""
  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .
  :                                                                   :
  :  ╔╦╗╔═╗╔╦╗╔═╗╔═╗╦ ╦╦╔╗╔╔═╗                                      :
  :  ║║║║╣  ║ ║ ║║  ╠═╣║║║║╠═╣                                       :
  :  ╩ ╩╚═╝ ╩ ╚═╝╚═╝╩ ╩╩╝╚╝╩ ╩                                      :
  :                                                                   :
  :  >>>  OSINT  /  METADATA  /  GEOLOCATION  /  ANALYSIS  <<<       :
  :  >>>  [CONNECTED]  //  SCANNING  //  ACTIVE  <<<                 :
  :                                                                   :
  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .  *  .
"""

# ──────────────────────────────────────────────
# Banner Style 5: Classic with decorative borders
# ──────────────────────────────────────────────
BANNER_CLASSIC = r"""
  +================================================================+
  |  ____    ____  ________  _________  ___   ___   ___  ____  ___ |
  | |    \  /    ||   _____||    _    ||   | |   | |   ||    \|   ||
  | |     \/     ||  |_____ |   | |   ||   |_|   | |   ||     \   ||
  | |   |\  /|   ||  |_____ |   | |   ||         | |   ||   |\    ||
  | |   | \/ |   ||   _____||   |_|   ||   ___   | |   ||   | \   ||
  | |___|    |___||________||_________||___| |___| |___||___|  \__||
  |                                                                |
  |       <<<  M E T O C H I N A  >>>  OSINT METADATA TOOL        |
  +================================================================+
"""

# Collect all banners
ALL_BANNERS = [
    BANNER_BLOCK,
    BANNER_SLANT,
    BANNER_GRAFFITI,
    BANNER_CYBER,
    BANNER_CLASSIC,
]


def get_random_banner() -> str:
    """Return a randomly selected ASCII art banner string."""
    return random.choice(ALL_BANNERS)


def _center(text: str, width: int = 80) -> str:
    """Center a string within a given width."""
    return text.center(width)


def print_banner(version: str = "1.2.0", author: str = "Belchite") -> None:
    """
    Print a random METOCHINA banner with color and metadata lines.

    Args:
        version: Version string to display.
        author:  Author name to display.
    """
    banner = get_random_banner()

    # Pick a highlight colour for the banner art
    art_color = random.choice([RED + BOLD, MAGENTA + BOLD])

    # Print the coloured banner
    for line in banner.splitlines():
        print(f"{art_color}{line}{RESET}")

    print()

    # Subtitle lines (centred)
    info_width = 80
    print(_center(f"{CYAN}OSINT Image Metadata Analyzer{RESET}", info_width + 9))
    print(_center(f"{DIM}{WHITE}v{version} | by {author}{RESET}", info_width + 13))
    print(_center(f"{DIM}{CYAN}github.com/Belchite/Metochina{RESET}", info_width + 13))

    # Spacing
    print()
    print()


def print_startup_sequence() -> None:
    """
    Print an animated startup sequence with colour and delays.
    """
    steps = [
        (f"{CYAN}[*]{RESET} Initializing Metochina...",      0.15),
        (f"{GREEN}[+]{RESET} Core engine loaded",             0.15),
        (f"{GREEN}[+]{RESET} GPS parser ready",               0.15),
        (f"{GREEN}[+]{RESET} Hash calculator ready",          0.15),
        (f"{GREEN}[+]{RESET} Risk analyzer ready",            0.15),
        (f"{GREEN}[+]{RESET} 7 analysis modules loaded",     0.15),
        (f"{GREEN}[+]{RESET} Ready.",                         0.15),
    ]

    print()
    for message, delay in steps:
        print(message)
        sys.stdout.flush()
        time.sleep(delay)
    print()


# ──────────────────────────────────────────────
# Quick self-test when run directly
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print_banner()
    print_startup_sequence()
