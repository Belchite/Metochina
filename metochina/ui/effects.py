"""Visual effects and animations for the Metochina hacker-style terminal UI."""

import os
import sys
import time
import itertools

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


def typing_effect(text: str, delay: float = 0.02) -> None:
    """Print text character by character with a delay between each."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def spinner(message: str, duration: float = 1.5) -> None:
    """Show a braille spinner rotating for *duration* seconds, then clear."""
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    cycle = itertools.cycle(frames)
    end_time = time.time() + duration
    while time.time() < end_time:
        frame = next(cycle)
        sys.stdout.write(f"\r{CYAN}{frame}{RESET} {message}")
        sys.stdout.flush()
        time.sleep(0.08)
    clear_line()


def progress_bar(current: int, total: int, width: int = 30, prefix: str = "") -> str:
    """Return a progress-bar string like ``[████████░░░░░░] 62% (241/389)``."""
    if total == 0:
        ratio = 1.0
    else:
        ratio = current / total
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(ratio * 100)
    result = f"{prefix}[{GREEN}{bar}{RESET}] {WHITE}{pct}%{RESET} ({current}/{total})"
    return result


def scanning_dots(message: str, steps: int = 3, delay: float = 0.3) -> None:
    """Print *message* with dots appearing one by one, then clear the line."""
    for i in range(1, steps + 1):
        sys.stdout.write(f"\r{CYAN}{message}{'.' * i}{RESET}")
        sys.stdout.flush()
        time.sleep(delay)
    clear_line()


def clear_line() -> None:
    """Clear the current terminal line."""
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()


def pause(message: str = "[*] Press Enter to return to menu...") -> None:
    """Display a colored prompt and wait for the user to press Enter."""
    input(f"\n{CYAN}{message}{RESET}")
