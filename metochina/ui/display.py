"""Visual formatting functions for the Metochina hacker-style terminal UI."""

import os
import sys
import re

# Enable ANSI escape codes on Windows
os.system("")

# ── ANSI codes ──────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
GRAY = "\033[90m"

# ── Helpers ─────────────────────────────────────────────────────────────────

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _visible_len(text: str) -> int:
    """Return the visible length of *text* (ignoring ANSI escape codes)."""
    return len(_ANSI_RE.sub("", text))


def _color_enabled() -> bool:
    """Check whether colour output should be used."""
    if os.environ.get("NO_COLOR"):
        return False
    if hasattr(sys.stdout, "isatty") and not sys.stdout.isatty():
        return False
    return True


def _c(code: str, text: str) -> str:
    """Wrap *text* in an ANSI colour *code* if colour is enabled."""
    if not _color_enabled():
        return text
    return f"{code}{text}{RESET}"


# ── Prefix functions ────────────────────────────────────────────────────────

def info(text: str) -> None:
    """Print an informational message with a ``[*]`` prefix."""
    print(f"{_c(CYAN, '[*]')} {text}")


def success(text: str) -> None:
    """Print a success message with a ``[+]`` prefix."""
    print(f"{_c(GREEN, '[+]')} {text}")


def error(text: str) -> None:
    """Print an error message with a ``[-]`` prefix."""
    print(f"{_c(RED, '[-]')} {text}")


def warning(text: str) -> None:
    """Print a warning message with a ``[!]`` prefix."""
    print(f"{_c(YELLOW, '[!]')} {text}")


def critical(text: str) -> None:
    """Print a critical message with a ``[!!]`` prefix."""
    print(f"{_c(RED + BOLD, '[!!]')} {text}")


def question(text: str) -> str:
    """Print a question with a ``[?]`` prefix and return the user's input."""
    return input(f"{_c(MAGENTA, '[?]')} {text}")


def result(key: str, value: str) -> None:
    """Print a key-value result with a ``[>]`` prefix."""
    print(f"{_c(WHITE + BOLD, '[>]')} {_c(WHITE, key)}  {_c(CYAN, value)}")


# ── Box-drawing (single line) ──────────────────────────────────────────────

def box_top(width: int = 55) -> str:
    """Return top border: ``┌───...───┐``."""
    return "┌" + "─" * (width - 2) + "┐"


def box_bottom(width: int = 55) -> str:
    """Return bottom border: ``└───...───┘``."""
    return "└" + "─" * (width - 2) + "┘"


def box_divider(width: int = 55) -> str:
    """Return a divider: ``├───...───┤``."""
    return "├" + "─" * (width - 2) + "┤"


def box_line(content: str, width: int = 55) -> str:
    """Return a box line with *content* padded to *width*."""
    inner = width - 4  # account for "│ " and " │"
    vis = _visible_len(content)
    pad = max(0, inner - vis)
    return f"│ {content}{' ' * pad} │"


def box_empty(width: int = 55) -> str:
    """Return an empty box line."""
    return "│" + " " * (width - 2) + "│"


def section_box(title: str, items: list, width: int = 55) -> None:
    """Render a complete section box with a title and key-value items.

    *items* is a list of ``(prefix, key, value)`` tuples.  Each *prefix*
    is a short tag like ``[>]`` or ``[+]``.
    """
    print(box_top(width))
    print(box_line(f"{_c(BOLD + WHITE, title)}", width))
    print(box_divider(width))
    for prefix, key, value in items:
        entry = f"{prefix} {_c(WHITE, key)}  {_c(CYAN, value)}"
        print(box_line(entry, width))
    print(box_bottom(width))


# ── Score bar ───────────────────────────────────────────────────────────────

def score_bar(score: int, width: int = 20) -> str:
    """Return a coloured score bar like ``████████░░░░ 45/100``.

    Colour:  green < 40,  yellow 40-70,  red >= 70.
    """
    clamped = max(0, min(score, 100))
    filled = int(width * clamped / 100)
    empty = width - filled

    if clamped < 40:
        colour = GREEN
    elif clamped <= 70:
        colour = YELLOW
    else:
        colour = RED

    bar = _c(colour, "█" * filled) + _c(GRAY, "░" * empty)
    return f"{bar} {_c(WHITE, str(score))}/100"


# ── Menu box (double-line) ──────────────────────────────────────────────────

def menu_box(title: str, items: list) -> None:
    """Render a double-line menu box.

    *items* is a list of ``(key, label, desc)`` tuples.
    ``key`` is the number/letter the user presses, ``label`` the action
    name, and ``desc`` a short description.
    """
    W = 60  # total width including border chars

    def _dbox_line(content: str) -> str:
        inner = W - 4  # "║ " and " ║"
        vis = _visible_len(content)
        pad = max(0, inner - vis)
        return f"║ {content}{' ' * pad} ║"

    top = "╔" + "═" * (W - 2) + "╗"
    div = "╠" + "═" * (W - 2) + "╣"
    bot = "╚" + "═" * (W - 2) + "╝"
    empty = "║" + " " * (W - 2) + "║"

    # Center the title
    vis_title = _visible_len(title)
    inner_w = W - 4
    left_pad = (inner_w - vis_title) // 2
    right_pad = inner_w - vis_title - left_pad
    centred = " " * left_pad + title + " " * right_pad

    print(top)
    print(f"║ {centred} ║")
    print(div)
    print(empty)

    for key, label, desc in items:
        entry = (
            f"  {_c(CYAN, '[' + str(key) + ']')}"
            f"  {_c(WHITE + BOLD, label.ljust(14))}"
            f" {_c(GRAY, '—')} {_c(GRAY, desc)}"
        )
        print(_dbox_line(entry))

    print(empty)
    exit_line = f"  {_c(CYAN, '[0]')}  {_c(WHITE + BOLD, 'Exit')}"
    print(_dbox_line(exit_line))
    print(empty)
    print(bot)
