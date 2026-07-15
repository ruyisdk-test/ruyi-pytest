import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, spawn_ruyi


# Shared i18n catalog for all repo tests
_REPO_CATALOG = {
    "zh_CN.UTF-8": {
        # add success
        "info: repo '{id}' added; run 'ruyi update' to sync":
            "信息：已添加软件包仓库 '{id}'；运行 'ruyi update' 以同步",
        # add errors
        "fatal error: invalid repo id '{id}'":
            "致命错误：无效的仓库 ID '{id}'",
        "fatal error: '{id}' is reserved; use [repo] config to configure the default repository":
            "致命错误：'{id}' 是保留的；请使用 [repo] 配置来配置默认仓库",
        "fatal error: at least one of URL or --local must be provided":
            "致命错误：URL 或 --local 至少需要提供一个",
        "fatal error: local path '{path}' must be absolute":
            "致命错误：本地路径 '{path}' 必须是绝对路径",
        "fatal error: a repo with id '{id}' already exists":
            "致命错误：已有一个 ID 为 '{id}' 的软件包仓库了",
        # remove
        "info: repo '{id}' removed":
            "信息：已移除软件包仓库 '{id}'",
        "fatal error: cannot remove the default repo '{id}'; use 'repo disable' instead":
            "致命错误：无法移除默认仓库 '{id}'；请使用 'repo disable' 来禁用它",
        "fatal error: no repo with id '{id}' found in user config":
            "致命错误：在用户配置中未找到 ID 为 '{id}' 的软件包仓库",
        # enable / disable
        "info: repo '{id}' enabled":
            "信息：已启用软件包仓库 '{id}'",
        "info: repo '{id}' disabled":
            "信息：已禁用软件包仓库 '{id}'",
        # set-priority
        "info: repo '{id}' priority set to {priority}":
            "信息：软件包仓库 '{id}' 的优先级已设置为 {priority}",
    },
}


def _suppress_telemetry(env: Dict[str, str]) -> None:
    """Suppress the first-run telemetry consent prompt."""
    telemetry_dir = Path(env["XDG_STATE_HOME"]) / "ruyi" / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    (telemetry_dir / "minimal-installation-marker").touch()


def test_ruyi_repo_list(ruyi_exe: str, isolated_env: Dict[str, str]):
    env = isolated_env
    _suppress_telemetry(env)

    # In a clean environment `ruyi repo list` should show the default repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "list"],
        env=env,
    )
    try:
        child.expect_exact("* ruyisdk")
        child.expect_exact("(default)")
        child.expect_exact("priority=0")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0


def test_ruyi_repo_add(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    env = isolated_env
    _suppress_telemetry(env)

    _ = bind_gettext(env, _REPO_CATALOG)

    # Add a valid repo with URL
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "test-repo", "https://github.com/xen0n/ruyi-addons-loongson"],
        env=env,
    )
    try:
        child.expect_exact(
            _("info: repo '{id}' added; run 'ruyi update' to sync").format(
                id="test-repo"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Verify it appears in list
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "list"],
        env=env,
    )
    try:
        child.expect_exact("test-repo")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Add with --name, --branch and --priority (URL must come before options)
    child = spawn_ruyi(
        ruyi_exe,
        [
            "repo", "add", "another-repo",
            "https://github.com/xen0n/ruyi-addons-loongson",
            "--name", "Another Repo",
            "--branch", "main",
            "--priority", "100",
        ],
        env=env,
    )
    try:
        child.expect_exact(
            _("info: repo '{id}' added; run 'ruyi update' to sync").format(
                id="another-repo"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Add with --local
    local_dir = tmp_path / "my-repo-local"
    local_dir.mkdir()

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "local-repo", "--local", str(local_dir)],
        env=env,
    )
    try:
        child.expect_exact(
            _("info: repo '{id}' added; run 'ruyi update' to sync").format(
                id="local-repo"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Verify local repo in list
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "list"],
        env=env,
    )
    try:
        child.expect_exact("local-repo")
        child.expect_exact(str(local_dir))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Error: invalid repo id (starts with uppercase)
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "Invalid", "https://github.com/xen0n/ruyi-addons-loongson"],
        env=env,
    )
    try:
        child.expect_exact(
            _("fatal error: invalid repo id '{id}'").format(id="Invalid")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1

    # Error: reserved repo id "ruyisdk"
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "ruyisdk", "https://github.com/xen0n/ruyi-addons-loongson"],
        env=env,
    )
    try:
        child.expect_exact(
            _(
                "fatal error: '{id}' is reserved; use  config to configure "
                "the default repository"
            ).format(id="ruyisdk")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1

    # Error: missing URL and --local
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "no-source-repo"],
        env=env,
    )
    try:
        child.expect_exact(
            _("fatal error: at least one of URL or --local must be provided")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1

    # Error: non-absolute --local path
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "bad-local-repo", "--local", "relative/path"],
        env=env,
    )
    try:
        child.expect_exact(
            _("fatal error: local path '{path}' must be absolute").format(
                path="relative/path"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1

    # Error: duplicate repo id
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "test-repo", "https://github.com/xen0n/ruyi-addons-loongson"],
        env=env,
    )
    try:
        child.expect_exact(
            _("fatal error: a repo with id '{id}' already exists").format(
                id="test-repo"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1


def test_ruyi_repo_remove(
    ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path
):
    env = isolated_env
    _suppress_telemetry(env)

    _ = bind_gettext(env, _REPO_CATALOG)

    # Pre-populate config with repo entries
    xdg_config = Path(env["XDG_CONFIG_HOME"])
    config_dir = xdg_config / "ruyi"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        '[[repos]]\n'
        'id = "remove-me"\n'
        'name = "Remove Me"\n'
        'remote = "https://github.com/xen0n/ruyi-addons-loongson"\n'
        'priority = 5\n'
        'active = true\n'
        '\n'
        '[[repos]]\n'
        'id = "purge-me"\n'
        'name = "Purge Me"\n'
        'remote = "https://github.com/xen0n/ruyi-addons-loongson"\n'
        'priority = 3\n'
        'active = true\n',
        encoding="utf-8",
    )

    # Confirm all entries are listed
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "list"],
        env=env,
    )
    try:
        child.expect_exact("remove-me")
        child.expect_exact("purge-me")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Remove the repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "remove-me"],
        env=env,
    )
    try:
        child.expect_exact(
            _("info: repo '{id}' removed").format(id="remove-me")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Remove with --purge (no cached data, but should still succeed)
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "purge-me", "--purge"],
        env=env,
    )
    try:
        child.expect_exact(
            _("info: repo '{id}' removed").format(id="purge-me")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Error: remove default repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "ruyisdk"],
        env=env,
    )
    try:
        child.expect_exact(
            _(
                "fatal error: cannot remove the default repo '{id}'; "
                "use 'repo disable' instead"
            ).format(id="ruyisdk")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1

    # Error: remove non-existent repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "nonexistent"],
        env=env,
    )
    try:
        child.expect_exact(
            _("fatal error: no repo with id '{id}' found in user config").format(
                id="nonexistent"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1


def test_ruyi_repo_enable_disable(
    ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path
):
    env = isolated_env
    _suppress_telemetry(env)

    _ = bind_gettext(env, _REPO_CATALOG)

    # Pre-populate config with a repo entry
    xdg_config = Path(env["XDG_CONFIG_HOME"])
    config_dir = xdg_config / "ruyi"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        '[[repos]]\n'
        'id = "toggle-me"\n'
        'name = "Toggle Me"\n'
        'remote = "https://github.com/xen0n/ruyi-addons-loongson"\n'
        'priority = 10\n'
        'active = true\n',
        encoding="utf-8",
    )

    # Disable the repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "disable", "toggle-me"],
        env=env,
    )
    try:
        child.expect_exact(
            _("info: repo '{id}' disabled").format(id="toggle-me")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Verify it's inactive (no `*` marker) in list
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "list"],
        env=env,
    )
    try:
        child.expect_exact("toggle-me")
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()

    assert child.exitstatus == 0
    # The toggle-me line should start with spaces (inactive), not `*`
    for line in output.splitlines():
        if "toggle-me" in line:
            assert not line.strip().startswith("* toggle-me")
            assert "  " in line[:4]  # two spaces before the id

    # Enable the repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "enable", "toggle-me"],
        env=env,
    )
    try:
        child.expect_exact(
            _("info: repo '{id}' enabled").format(id="toggle-me")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Verify it's active again
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "list"],
        env=env,
    )
    try:
        child.expect_exact("toggle-me")
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()

    assert child.exitstatus == 0
    for line in output.splitlines():
        if "toggle-me" in line:
            assert "* toggle-me" in line

    # Error: enable non-existent repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "enable", "nonexistent"],
        env=env,
    )
    try:
        child.expect_exact(
            _("fatal error: no repo with id '{id}' found in user config").format(
                id="nonexistent"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1

    # Error: disable non-existent repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "disable", "nonexistent"],
        env=env,
    )
    try:
        child.expect_exact(
            _("fatal error: no repo with id '{id}' found in user config").format(
                id="nonexistent"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1


def test_ruyi_repo_set_priority(
    ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path
):
    env = isolated_env
    _suppress_telemetry(env)

    _ = bind_gettext(env, _REPO_CATALOG)

    # Pre-populate config with a repo entry
    xdg_config = Path(env["XDG_CONFIG_HOME"])
    config_dir = xdg_config / "ruyi"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        '[[repos]]\n'
        'id = "priority-repo"\n'
        'name = "Priority Repo"\n'
        'remote = "https://github.com/xen0n/ruyi-addons-loongson"\n'
        'priority = 10\n'
        'active = true\n',
        encoding="utf-8",
    )

    # Set priority
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "set-priority", "priority-repo", "999"],
        env=env,
    )
    try:
        child.expect_exact(
            _("info: repo '{id}' priority set to {priority}").format(
                id="priority-repo", priority=999
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Verify the priority in list output
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "list"],
        env=env,
    )
    try:
        child.expect_exact("priority-repo")
        child.expect_exact("priority=999")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # Error: set priority on non-existent repo
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "set-priority", "nonexistent", "100"],
        env=env,
    )
    try:
        child.expect_exact(
            _("fatal error: no repo with id '{id}' found in user config").format(
                id="nonexistent"
            )
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1
