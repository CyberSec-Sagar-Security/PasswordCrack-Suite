"""
Main entry point for PasswordCrack Suite GUI.

Launches the graphical user interface.
"""

import sys
from .ui.gui_app import main as gui_main


def main() -> int:
    """
    Main entry point for the GUI application.
    
    Returns:
        Exit code (0 for success)
    """
    try:
        gui_main()
        return 0
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
