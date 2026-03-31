# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an LLM plugin (`llm-tools-sandboxed-shell`) that provides secure, sandboxed execution of terminal commands for Simon Willison's LLM tool. The plugin uses bubblewrap to create isolated environments where commands cannot modify the host system, access the network, or leak data.

## Development Commands

### Setup
```bash
# Install in development mode with test dependencies
python -m pip install -e '.[test]'
```

### Testing
```bash
# Run all tests
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run a specific test
python -m pytest tests/test_tools_sandboxed_shell.py::test_basic_command_execution

# Run tests with coverage
python -m pytest --cov=llm_tools_sandboxed_shell
```

### Local Testing of Plugin
```bash
# After installing in development mode, the plugin is automatically available to llm
# Test it interactively with a model that supports tools
llm chat -m <model-name>
# Then ask the model to execute a sandboxed command
```

## Architecture

This is a single-file plugin. All logic lives in `llm_tools_sandboxed_shell.py`.

### Plugin Registration
The plugin uses the LLM framework's `register_tools` hook (via `@llm.hookimpl`) to register the `sandboxed_shell` function as a tool. The entry point is configured in `pyproject.toml` under `[project.entry-points.llm]`.

### Core Function: `sandboxed_shell(command: str) -> str`
Constructs a bubblewrap command, executes the user's shell command inside it, and returns stdout/stderr combined with exit codes when non-zero. Never raises exceptions — all errors are returned as formatted strings.

### Bubblewrap Security Model

- **Read-only filesystem**: `--ro-bind / /` makes the entire host visible but not modifiable
- **Namespace isolation**: `--unshare-pid`, `--unshare-cgroup`, `--unshare-ipc`, `--unshare-uts`, `--unshare-net`
- **Capability drop**: `--cap-drop ALL` for maximum restriction
- **Environment isolation**: `--clearenv` then selectively passes safe vars (PATH, HOME, USER, locale, etc.)
- **Temporary areas**: `/tmp` (1GB size limit), `/var`, `/run` are tmpfs, non-persistent
- **Process management**: `--die-with-parent`, `--new-session`

### Testing Notes

- Tests call `sandboxed_shell()` directly (no mocking of subprocess/bubblewrap)
- The timeout test (`test_timeout_handling`) is skipped by default (takes 60+ seconds)

## System Requirements

- **bubblewrap**: Must be installed (`apt-get install bubblewrap` on Debian/Ubuntu)
- **Python**: Requires Python 3.10+
- **Linux**: Bubblewrap requires Linux kernel namespaces

## Key Design Decisions

1. **Read-only host filesystem**: The entire host filesystem is visible but read-only. This allows commands to examine real system files while preventing modifications.
2. **60-second timeout**: Commands are automatically killed after 60 seconds to prevent resource exhaustion.
3. **Combined output**: stdout and stderr are combined in the return value for simplicity, with stderr clearly labeled.
4. **No exceptions to caller**: All errors (timeout, missing bwrap, execution failures) are returned as formatted strings, never raised.
