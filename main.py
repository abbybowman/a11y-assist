"""Root entry point for local development.

Run locally:
    uv run python main.py

Or via the installed script:
    uv run a11y-assist
"""

from a11y_assist.app import main

if __name__ == "__main__":
    main()
