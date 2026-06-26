
import pexpect

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_config(ruyi_exe: str, isolated_env: Dict[str, str]):
    """Test `ruyi config get/set/unset/remove-section` subcommands."""
    _ = bind_gettext(isolated_env, {})
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # Set repo.remote
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "repo.remote", "https://example.com/repo"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Get repo.remote
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "get", "repo.remote"],
        env=isolated_env,
    )
    try:
        child.expect_exact("https://example.com/repo")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Set packages.prereleases to true (bool type)
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "packages.prereleases", "true"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Get packages.prereleases
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "get", "packages.prereleases"],
        env=isolated_env,
    )
    try:
        child.expect_exact("true")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Set repo.branch to develop (string type)
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "repo.branch", "develop"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Get repo.branch
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "get", "repo.branch"],
        env=isolated_env,
    )
    try:
        child.expect_exact("develop")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Unset repo.remote
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "unset", "repo.remote"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Get repo.remote (after unset, default is None → exit code 1)
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "get", "repo.remote"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # Remove the entire packages section
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "remove-section", "packages"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Get packages.prereleases (after section removal, defaults to false)
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "get", "packages.prereleases"],
        env=isolated_env,
    )
    try:
        child.expect_exact("false")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Invalid config key → exit code 1
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "get", "invalid.key"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # Protected global-only config key → exit code 2
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "installation.externally_managed", "true"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 2


def test_ruyi_config_error_cases(ruyi_exe: str, isolated_env: Dict[str, str]):
    """Test edge cases and error scenarios for `ruyi config` subcommands."""
    _ = bind_gettext(isolated_env, {})
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # Unset a key that does not exist (should be no-op, exit code 0)
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "unset", "packages.prereleases"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Remove a section that does not exist (should be no-op, exit code 0)
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "remove-section", "installation"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Set invalid value type for a bool key → exit code 1
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "packages.prereleases", "notabool"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # Set packages.prereleases to false
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "packages.prereleases", "false"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Get packages.prereleases → verify it is false
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "get", "packages.prereleases"],
        env=isolated_env,
    )
    try:
        child.expect_exact("false")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Set telemetry.mode to valid value "on"
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "telemetry.mode", "on"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Get telemetry.mode → verify it is "on"
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "get", "telemetry.mode"],
        env=isolated_env,
    )
    try:
        child.expect_exact("on")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # Set telemetry.mode to invalid value → exit code 1
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "telemetry.mode", "invalid_mode"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # Set an invalid config key → exit code 1
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "nonexist.section", "value"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # Unset an invalid key → exit code 1
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "unset", "nonexist.section"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # Remove an invalid section → exit code 1
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "remove-section", "nonexist"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1
