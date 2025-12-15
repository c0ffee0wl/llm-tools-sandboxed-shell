"""
LLM plugin for executing terminal commands in a sandboxed environment using bubblewrap.

This plugin provides secure command execution by isolating processes in a sandbox where:
- No files on the host system can be modified
- No network access is possible
- Commands run in an isolated namespace environment
"""

import subprocess
import shlex
import os
import llm
from typing import Optional


def sandboxed_shell(command: str) -> str:
    """
    Execute a shell command in a secure bubblewrap sandbox.

    Runs commands with full filesystem visibility but no write access, useful for
    safely exploring the system, reading files, or running diagnostic commands.
    Commands cannot modify files, access the network, or affect host processes.

    Sandbox security features:
    - Read-only access to entire host filesystem (visible but not modifiable)
    - No network access (--unshare-net)
    - Isolated PID, IPC, and cgroup namespaces
    - Temporary /tmp, /var and /run directories that don't persist
    - Real user HOME, USER, and PWD from host environment

    Args:
        command: The shell command to execute (e.g., "ls -la", "cat /etc/hostname",
                 "grep -r pattern /path"). Multi-command pipes supported.

    Returns:
        Command output (stdout + stderr). Exit code shown if non-zero.
        Timeout after 60 seconds.
    """

    # Get current user ID for runtime directory
    uid = os.getuid()

    # Build the secure bubblewrap command
    bwrap_args = [
        'bwrap',
        
        # Die if parent process dies
        '--die-with-parent',

        # Mount entire filesystem as read-only
        '--ro-bind', '/', '/',

        # Mount /dev and /proc for command functionality
        '--dev', '/dev',
        '--proc', '/proc',

        # Create temporary filesystems for system directories
        '--tmpfs', '/tmp',
        '--tmpfs', '/var',
        '--tmpfs', '/run',
        '--dir', f'/run/user/{uid}',

        # Isolate specific namespaces
        '--unshare-pid',     # Isolate process namespace
        '--unshare-cgroup',  # Isolate cgroup namespace
        '--unshare-ipc',     # Isolate IPC namespace
        '--unshare-net',     # Block network access

        # Drop all capabilities for maximum security
        '--cap-drop', 'ALL',

        # Clear environment for isolation
        '--clearenv',

        # Set essential environment variables
        '--setenv', 'PATH', os.environ.get('PATH', '/usr/bin:/bin:/usr/sbin:/sbin'),
        '--setenv', 'HOME', os.environ.get('HOME', '/tmp'),
        '--setenv', 'USER', os.environ.get('USER', 'sandbox'),
    ]

    # Add safe display/locale environment variables
    safe_env_vars = ['LANG', 'COLORTERM', 'EDITOR', 'VISUAL', 'PAGER']
    for var in safe_env_vars:
        if var in os.environ:
            bwrap_args.extend(['--setenv', var, os.environ[var]])

    # Add all LC_* locale variables
    for var, value in os.environ.items():
        if var.startswith('LC_'):
            bwrap_args.extend(['--setenv', var, value])

    # Add final arguments
    bwrap_args.extend([
        # Set working directory to current directory
        '--chdir', os.environ.get('PWD', '/tmp'),

        # Create new session
        '--new-session',

        # The command to execute
        '--',
        '/bin/sh',
        '-c',
        command
    ])

    try:
        # Execute the sandboxed command
        result = subprocess.run(
            bwrap_args,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout to prevent hanging
            check=False  # Don't raise exception on non-zero exit
        )

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]:\n" + result.stderr

        # Add exit code information
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"

        return output if output else "[No output]"

    except subprocess.TimeoutExpired:
        return "[Error: Command timed out after 60 seconds]"
    except FileNotFoundError:
        return "[Error: bubblewrap (bwrap) not found. Please install bubblewrap: apt-get install bubblewrap]"
    except Exception as e:
        return f"[Error executing command: {str(e)}]"


@llm.hookimpl
def register_tools(register):
    """Register the sandboxed shell execution tool."""
    register(sandboxed_shell)
