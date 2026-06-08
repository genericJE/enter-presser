# enter-presser

A tiny command-line tool that waits for a specified number of minutes, then presses Enter/Return in the currently focused application.

Usage:

    uv run enter-presser -t 23

Dry run test:

    uv run enter-presser -t 0.05 --dry-run

Multiple presses:

    uv run enter-presser -t 23 --count 3 --interval 2

Setup:

    uv sync
    uv run enter-presser --help

macOS permissions:

On macOS, the terminal app running this command may need Accessibility permission.

Go to:

System Settings -> Privacy & Security -> Accessibility

Enable Terminal, iTerm, Ghostty, or whichever terminal you use.
