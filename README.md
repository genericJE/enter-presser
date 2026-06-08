# enter-presser

A tiny command-line tool that waits for a specified number of minutes, then presses Enter/Return in the currently focused application.

## Install with Homebrew

```bash
brew tap genericJE/tools
brew install enter-presser
```

## Usage:

```bash
enter-presser 23  # 23 minutes
enter-presser 01:02:03  # HH:MM:SS format -> Waiting 1 hour 2 minutes and 3 seconds
```

### Dry run test:

```bash
enter-presser 0.05 --dry-run  # 3 seconds
```

### Multiple presses:

```bash
enter-presser 23 --count 3 --interval 2  # Presses enter 3 times with a 2 second interval between after 23 minutes of wainting
```

## Development Setup:

```bash
uv sync
uv run enter-presser --help
```

## macOS permissions:

On macOS, the terminal app running this command may need Accessibility permission.

Go to:
`System Settings` -> `Privacy & Security` -> `Accessibility`
Enable Terminal, iTerm, Ghostty, or whichever terminal you use.
