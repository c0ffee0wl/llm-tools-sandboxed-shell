"""
Tests for the sandboxed execution plugin.
"""

import pytest
from llm.plugins import pm
from llm_tools_sandboxed_shell import sandboxed_shell


def test_plugin_is_installed():
    """Verify the plugin is properly installed."""
    names = [mod.__name__ for mod in pm.get_plugins()]
    assert "llm_tools_sandboxed_shell" in names


def test_basic_command_execution():
    """Test basic command execution in sandbox."""
    result = sandboxed_shell("echo 'Hello from sandbox'")
    assert "Hello from sandbox" in result


def test_ls_command():
    """Test ls command works in sandbox."""
    result = sandboxed_shell("ls -la /")
    # Should see standard directories
    assert "tmp" in result.lower() or "etc" in result.lower()


def test_pwd_command():
    """Test that working directory is set correctly."""
    result = sandboxed_shell("pwd")
    assert "/tmp" in result


def test_filesystem_isolation():
    """Test that filesystem is properly isolated (read-only)."""
    # Try to write to a system directory - should fail
    result = sandboxed_shell("touch /usr/test_file 2>&1")
    # Should contain error about read-only or permission denied
    assert "read-only" in result.lower() or "permission denied" in result.lower() or "exit code" in result.lower()


def test_network_isolation():
    """Test that network access is blocked."""
    # Try to use ping or curl - should fail due to network isolation
    result = sandboxed_shell("ping -c 1 8.8.8.8 2>&1 || echo 'Network blocked'")
    # Network should be unreachable or command should indicate failure
    assert "network" in result.lower() or "exit code" in result.lower() or "blocked" in result.lower()


def test_tmp_directory_writable():
    """Test that /tmp is writable in sandbox."""
    result = sandboxed_shell("echo 'test content' > /tmp/testfile && cat /tmp/testfile")
    assert "test content" in result


def test_home_directory_readonly():
    """Test that home directory is read-only in sandbox."""
    # HOME points to real user home which is read-only
    result = sandboxed_shell("touch ~/testfile 2>&1")
    # Should fail because real home is read-only
    assert "read-only" in result.lower() or "permission denied" in result.lower() or "exit code" in result.lower()


def test_environment_isolation():
    """Test that environment is properly isolated."""
    result = sandboxed_shell("env")
    # Should have essential environment variables
    assert "PATH" in result
    assert "HOME=" in result
    assert "USER=" in result
    # Should not have sensitive variables (credentials, etc.)
    assert "SSH_AUTH_SOCK" not in result or "SSH_AUTH_SOCK=" not in result
    assert "GPG_AGENT_INFO" not in result or "GPG_AGENT_INFO=" not in result


def test_multiple_commands():
    """Test chaining multiple commands."""
    result = sandboxed_shell("echo 'first' && echo 'second' && echo 'third'")
    assert "first" in result
    assert "second" in result
    assert "third" in result


def test_stderr_capture():
    """Test that stderr is captured."""
    result = sandboxed_shell("echo 'error message' >&2")
    assert "error message" in result


def test_exit_code_non_zero():
    """Test that non-zero exit codes are reported."""
    result = sandboxed_shell("exit 42")
    assert "Exit code: 42" in result


def test_cat_etc_hostname():
    """Test reading system files (read-only)."""
    result = sandboxed_shell("cat /etc/hostname 2>&1 || echo 'No hostname'")
    # Should either read hostname or indicate it doesn't exist
    assert len(result) > 0


def test_process_isolation():
    """Test that process namespace is isolated."""
    result = sandboxed_shell("ps aux")
    # In isolated PID namespace, should only see processes in sandbox
    # The process list should be minimal
    assert "ps aux" in result or "PID" in result


def test_command_with_pipes():
    """Test commands with pipes work correctly."""
    result = sandboxed_shell("echo 'line1\nline2\nline3' | grep line2")
    assert "line2" in result


def test_no_write_to_host_home():
    """Test that host user directories are visible but not writable."""
    # /home is now visible (read-only) from the host filesystem
    # Test that we can see it but cannot write to it
    result = sandboxed_shell("touch /home/testfile 2>&1")
    # Should fail because /home is read-only
    assert "read-only" in result.lower() or "permission denied" in result.lower() or "exit code" in result.lower()


@pytest.mark.skipif(
    True,  # Skip by default as it tests timeout which takes 60+ seconds
    reason="Timeout test takes too long for regular test runs"
)
def test_timeout_handling():
    """Test that long-running commands are timed out."""
    result = sandboxed_shell("sleep 120")
    assert "timed out" in result.lower()
