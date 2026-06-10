# enter-presser

A tiny command-line tool that waits for a set amount of time, showing a live countdown, then presses Enter/Return in the currently focused application. It can optionally type a message first.

## Install with Homebrew

```bash
brew tap genericJE/tools
brew install enter-presser
```

## Usage:

```bash
enter-presser 23  # 23 seconds
enter-presser 02:30  # MM:SS format -> 2 minutes 30 seconds
enter-presser 01:02:03  # HH:MM:SS format -> 1 hour 2 minutes 3 seconds
```

### Dry run test:

```bash
enter-presser 3 --dry-run  # 3 seconds
```

### Multiple presses:

```bash
enter-presser 23 --count 3 --interval 2  # Presses enter 3 times with a 2 second interval, after waiting 23 seconds
```

### Type a message before pressing Enter:

Use `-m`/`--message` to type some text into the focused app just before Enter is pressed. Characters are sent one at a time with a short delay so the app does not drop any.

```bash
enter-presser 23 -m "Hello there"  # Wait 23 seconds, type "Hello there", then press Enter
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
