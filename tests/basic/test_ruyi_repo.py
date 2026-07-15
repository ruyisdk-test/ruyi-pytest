import pexpect

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_repo(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: 'ruyisdk' is reserved; use [repo] config to configure the default repositor":
                "致命错误：'ruyisdk' 是保留的；请使用 [repo] 配置来配置默认仓库",
            "info: repo 'ruyi-addons-loongson' added; run 'ruyi update' to sync":
                "信息：已添加软件包仓库 'ruyi-addons-loongson'；运行 'ruyi update' 以同步",
            "info: syncing repo 'ruyisdk'": "信息：正在同步仓库 'ruyisdk'",
            "info: syncing repo 'ruyi-addons-loongson'":
                "信息：正在同步仓库 'ruyi-addons-loongson'",
            "warn: repo 'ruyi-addons-loongson' declares id 'test-loongson' in its config.toml; expected 'ruyi-addons-loongson'":
                "警告：仓库 'ruyi-addons-loongson' 在其 config.toml 中声明了 id 'test-loongson'；预期为 'ruyi-addons-loongson'",
            "info: repo 'ruyi-addons-loongson' enabled": "信息：已启用软件包仓库 'ruyi-addons-loongson'",
            "info: repo 'ruyi-addons-loongson' disabled": "信息：已禁用软件包仓库 'ruyi-addons-loongson'",
            "fatal error: no active repo with id 'ruyi-addons-loongson'":
                "致命错误：没有 ID 为 'ruyi-addons-loongson' 的活动仓库",
            "info: repo 'ruyi-addons-loongson' priority set to 20": "信息：软件包仓库 'ruyi-addons-loongson' 的优先级已设置为 20",
            "info: repo 'ruyi-addons-loongson' removed": "信息：已移除软件包仓库 'ruyi-addons-loongson'",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi repo list
    child = spawn_ruyi(ruyi_exe, ["repo", "list"], env=isolated_env)
    try:
        child.expect_exact("* ruyisdk (default)  priority=0")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi repo add ruyisdk https://
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "ruyisdk", "https://github.com/xen0n/ruyi-addons-loongson.git"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: 'ruyisdk' is reserved; use [repo] config to configure the default repositor"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # ruyi repo add ruyi-addons-loongson https://github.com/xen0n/ruyi-addons-loongson.git
    child = spawn_ruyi(
        ruyi_exe,
        [
            "repo", "add", "ruyi-addons-loongson", "https://github.com/xen0n/ruyi-addons-loongson.git",
            "--branch", "main", "--priority", "10", "--name", "loongson addon",
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' added; run 'ruyi update' to sync"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi update
    child = spawn_ruyi(
        ruyi_exe,
        ["update"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("info: syncing repo 'ruyi-addons-loongson'"))
        child.expect_exact(_("warn: repo 'ruyi-addons-loongson' declares id 'test-loongson' in its config.toml; expected 'ruyi-addons-loongson'"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo list
    child = spawn_ruyi(ruyi_exe, ["repo", "list"], env=isolated_env)
    try:
        child.expect_exact("ruyi-addons-loongson  priority=10  https://github.com/xen0n/ruyi-addons-loongson.git")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi repo enable ruyi-addons-loongson
    child = spawn_ruyi(ruyi_exe, ["repo", "enable", "ruyi-addons-loongson"], env=isolated_env)
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' enabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi repo disable ruyi-addons-loongson
    child = spawn_ruyi(ruyi_exe, ["repo", "disable", "ruyi-addons-loongson"], env=isolated_env)
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' disabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi update --repo ruyi-addons-loongson
    child = spawn_ruyi(
        ruyi_exe,
        ["update", "--repo", "ruyi-addons-loongson"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: no active repo with id 'ruyi-addons-loongson'"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo set-priority ruyi-addons-loongson 20
    child = spawn_ruyi(ruyi_exe, ["repo", "set-priority", "ruyi-addons-loongson", "20"], env=isolated_env)
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' priority set to 20"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi repo list
    child = spawn_ruyi(ruyi_exe, ["repo", "list"], env=isolated_env)
    try:
        child.expect_exact("ruyi-addons-loongson  priority=20  https://github.com/xen0n/ruyi-addons-loongson.git")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi repo remove ruyi-addons-ruyi-addons-loongson
    child = spawn_ruyi(ruyi_exe, ["repo", "remove", "ruyi-addons-loongson"], env=isolated_env)
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' removed"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi repo list
    child = spawn_ruyi(ruyi_exe, ["repo", "list"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert "ruyi-addons-loongson" not in child.before
    finally:
        child.close()
    assert child.exitstatus == 0


def test_ruyi_repo_default(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: no repo with id 'ruyisdk' found in user config":
                "致命错误：在用户配置中未找到 ID 为 'ruyisdk' 的软件包仓库",
            "fatal error: cannot remove the default repo 'ruyisdk'; use 'repo disable' instead":
                "致命错误：无法移除默认仓库 'ruyisdk'；请使用 'repo disable' 来禁用它",
            "info: repo 'ruyisdk' enabled": "信息：已启用软件包仓库 'ruyisdk'",
            "info: repo 'ruyisdk' disabled": "信息：已禁用软件包仓库 'ruyisdk'"
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi update --repo ruyisdk
    child = spawn_ruyi(
        ruyi_exe,
        ["update", "--repo", "ruyisdk"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo remove ruyisdk
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "ruyisdk"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("fatal error: cannot remove the default repo 'ruyisdk'; use 'repo disable' instead"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo disable ruyisdk
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "disable", "ruyisdk"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("info: repo 'ruyisdk' disabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo enable ruyisdk
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "enable", "ruyisdk"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("info: repo 'ruyisdk' enabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo set-priority ruyisdk 20
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "set-priority", "ruyisdk", "20"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("fatal error: no repo with id 'ruyisdk' found in user config"))
        child.expect(pexpect.EOF)
    finally:
        child.close()


def test_ruyi_repo_error_cases(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: no active repo with id 'no-id'":
                "致命错误：没有 ID 为 'no-id' 的活动仓库",
            "fatal error: no repo with id 'no-id' found in user config":
                "致命错误：在用户配置中未找到 ID 为 'no-id' 的软件包仓库",
            "fatal error: a repo with id 'dup' already exists":
                "致命错误：已有一个 ID 为 'dup' 的软件包仓库了"
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi update --repo no-id
    child = spawn_ruyi(
        ruyi_exe,
        ["update", "--repo", "no-id"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: no active repo with id 'no-id'"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo remove no-id
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "no-id"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("fatal error: no repo with id 'no-id' found in user config"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo disable no-id
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "disable", "no-id"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("fatal error: no repo with id 'no-id' found in user config"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo enable no-id
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "enable", "no-id"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("fatal error: no repo with id 'no-id' found in user config"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo set-priority no-id 20
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "set-priority", "no-id", "20"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_("fatal error: no repo with id 'no-id' found in user config"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # ruyi repo add bad-priority https://example.com/repo.git --priority not-an-int
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "bad-priority", "https://example.com/repo.git", "--priority", "not-an-int"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 2

    # ruyi repo add dup https://example.com/repo.git
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "dup", "https://example.com/repo.git"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi repo add dup https://example.com/repo.git
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "dup", "https://example.com/repo.git"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: a repo with id 'dup' already exists"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1
