"""Allow running metochina as a module: python -m metochina.

If called without arguments: launches the interactive hacker-style terminal UI.
If called with arguments: uses the standard Click CLI interface.
"""

import sys


def main() -> None:
    if len(sys.argv) <= 1:
        # No arguments — launch interactive UI
        from metochina.ui.menu import run_interactive
        run_interactive()
    else:
        # Arguments provided — use the Click CLI
        from metochina.cli import cli
        cli()


if __name__ == "__main__":
    main()
