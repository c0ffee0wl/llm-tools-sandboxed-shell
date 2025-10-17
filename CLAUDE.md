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

### Plugin Registration
The plugin uses the LLM framework's `register_tools` hook (defined via `@llm.hookimpl`) to register the `sandboxed_shell` function as a tool. The entry point is configured in `pyproject.toml` under `[project.entry-points.llm]`.

### Core Function: `sandboxed_shell(command: str) -> str`
Located in `llm_tools_sandboxed_shell.py`, this is the main tool function that LLM models can invoke. It:

1. Constructs a secure bubblewrap command that makes the entire filesystem visible (read-only)
2. Executes the user's shell command inside the sandbox with the user's current working directory
3. Returns stdout/stderr combined, with exit codes when non-zero

### Bubblewrap Security Configuration

The sandbox configuration balances security with filesystem visibility:

- **Read-only filesystem**: Entire root filesystem (`/`) is mounted read-only with `--ro-bind / /`, making all host files visible but not modifiable
- **Namespace isolation**: Selective namespace isolation with `--unshare-pid`, `--unshare-cgroup`, `--unshare-ipc`, and `--unshare-net`
- **Network isolation**: `--unshare-net` prevents all network access
- **Temporary system areas**: `/var` and `/run` are tmpfs that don't persist across invocations
- **Environment isolation**: `--clearenv` clears all environment variables, then passes through safe ones (PATH, HOME, USER, TERM, LANG, LC_*, SHELL, EDITOR, etc.)
- **Process management**: `--die-with-parent` ensures sandbox processes terminate if parent dies

### Error Handling Strategy

The `sandboxed_shell` function never raises exceptions to the caller. All errors are returned as formatted strings:
- Timeout errors (60s limit)
- Missing bubblewrap installation
- General execution errors
- Non-zero exit codes are appended to output

### Testing Philosophy

Tests in `tests/test_tools_sandboxed_shell.py` validate:
- Basic command execution functionality
- Security isolation (filesystem read-only, network blocked, environment cleared)
- Writable temporary directories work correctly
- Error handling and edge cases
- One long-running timeout test is skipped by default to keep test suite fast

## System Requirements

- **bubblewrap**: Must be installed (`apt-get install bubblewrap` on Debian/Ubuntu)
- **Python**: Requires Python 3.10+
- **Linux**: Bubblewrap requires Linux kernel namespaces

## Key Design Decisions

1. **Read-only host filesystem**: The entire host filesystem is visible but read-only (via `--ro-bind / /`). This allows commands to examine real system files while preventing modifications.

3. **60-second timeout**: Commands are automatically killed after 60 seconds to prevent resource exhaustion.

4. **Combined output**: stdout and stderr are combined in the return value for simplicity, with stderr clearly labeled.

5. **Defensive security**: The configuration assumes hostile input and provides defense-in-depth through namespace isolation, network blocking, and environment clearing.
