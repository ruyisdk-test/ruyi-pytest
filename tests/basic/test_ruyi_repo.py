import json
import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import (
    bind_gettext,
    ruyi_init_default_telemetry,
    spawn_ruyi,
    xfail_known_ruyi_defect,
)


def test_ruyi_repo(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: 'ruyisdk' is reserved; use [repo] config to configure the default repositor":
                "致命错误：'ruyisdk' 是保留的；请使用 [repo] 配置来配置默认仓库",
            "info: repo 'ruyi-addons-loongson' added; run 'ruyi update' to sync":
                "信息：已添加软件包仓库 'ruyi-addons-loongson'；运行 'ruyi update' 以同步",
            "info: syncing repo 'ruyi-addons-loongson'":
                "信息：正在同步仓库 'ruyi-addons-loongson'",
            "warn: repo 'ruyi-addons-loongson' declares id 'test-loongson' in its config.toml; expected 'ruyi-addons-loongson'":
                "警告：仓库 'ruyi-addons-loongson' 在其 config.toml 中声明了 id 'test-loongson'；预期为 'ruyi-addons-loongson'",
            "info: repo 'ruyi-addons-loongson' enabled":
                "信息：已启用软件包仓库 'ruyi-addons-loongson'",
            "info: repo 'ruyi-addons-loongson' disabled":
                "信息：已禁用软件包仓库 'ruyi-addons-loongson'",
            "fatal error: no active repo with id 'ruyi-addons-loongson'":
                "致命错误：没有 ID 为 'ruyi-addons-loongson' 的活动仓库",
            "info: repo 'ruyi-addons-loongson' priority set to 20":
                "信息：软件包仓库 'ruyi-addons-loongson' 的优先级已设置为 20",
            "info: repo 'ruyi-addons-loongson' removed":
                "信息：已移除软件包仓库 'ruyi-addons-loongson'",
        },
    })
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(ruyi_exe, ["repo", "list"], env=isolated_env)
    try:
        child.expect_exact("* ruyisdk (default)  priority=0")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

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

    child = spawn_ruyi(
        ruyi_exe,
        [
            "repo", "add", "ruyi-addons-loongson",
            "https://github.com/xen0n/ruyi-addons-loongson.git",
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

    child = spawn_ruyi(ruyi_exe, ["update"], env=isolated_env, timeout=60)
    try:
        child.expect_exact(_("info: syncing repo 'ruyi-addons-loongson'"))
        child.expect_exact(_("warn: repo 'ruyi-addons-loongson' declares id 'test-loongson' in its config.toml; expected 'ruyi-addons-loongson'"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["repo", "list"], env=isolated_env)
    try:
        child.expect_exact("ruyi-addons-loongson  priority=10  https://github.com/xen0n/ruyi-addons-loongson.git")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "enable", "ruyi-addons-loongson"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' enabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "disable", "ruyi-addons-loongson"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' disabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

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
    assert child.exitstatus == 1

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "set-priority", "ruyi-addons-loongson", "20"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' priority set to 20"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["repo", "list"], env=isolated_env)
    try:
        child.expect_exact("ruyi-addons-loongson  priority=20  https://github.com/xen0n/ruyi-addons-loongson.git")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "ruyi-addons-loongson"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: repo 'ruyi-addons-loongson' removed"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

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
            "info: repo 'ruyisdk' disabled": "信息：已禁用软件包仓库 'ruyisdk'",
        },
    })
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

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
    assert child.exitstatus == 0

    for args, message, exitstatus in (
        (["repo", "remove", "ruyisdk"],
         "fatal error: cannot remove the default repo 'ruyisdk'; use 'repo disable' instead", 1),
        (["repo", "disable", "ruyisdk"], "info: repo 'ruyisdk' disabled", 0),
        (["repo", "enable", "ruyisdk"], "info: repo 'ruyisdk' enabled", 0),
        (["repo", "set-priority", "ruyisdk", "20"],
         "fatal error: no repo with id 'ruyisdk' found in user config", 1),
    ):
        child = spawn_ruyi(ruyi_exe, args, env=isolated_env)
        try:
            child.expect_exact(_(message))
            child.expect(pexpect.EOF)
        finally:
            child.close()
        assert child.exitstatus == exitstatus


def test_ruyi_repo_local_and_porcelain(
    ruyi_exe: str,
    isolated_env: Dict[str, str],
    tmp_path: Path,
):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        [
            "repo", "add", "test", "https://example.com/repo.git",
            "--branch", "main", "--priority", "10", "--name", "Test Repo",
        ],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["--porcelain", "repo", "list"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        records = [json.loads(line) for line in child.before.splitlines() if line]
    finally:
        child.close()
    assert child.exitstatus == 0
    entry = next(record for record in records if record["id"] == "test")
    assert entry == {
        "ty": "repoentry-v1",
        "id": "test",
        "name": "Test Repo",
        "remote": "https://example.com/repo.git",
        "branch": "main",
        "local_path": None,
        "priority": 10,
        "active": True,
        "is_system": False,
    }

    local_repo = tmp_path / "local repo"
    local_repo.mkdir()
    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "local", "--local", str(local_repo), "--name", "Local Repo"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["--porcelain", "repo", "list"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        records = [json.loads(line) for line in child.before.splitlines() if line]
    finally:
        child.close()
    assert child.exitstatus == 0
    entry = next(record for record in records if record["id"] == "local")
    assert entry["name"] == "Local Repo"
    assert entry["remote"] == ""
    assert entry["local_path"] == str(local_repo)
    assert entry["active"] is True

    child = spawn_ruyi(ruyi_exe, ["repo", "remove", "local"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert local_repo.exists()

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "purge-me", "https://example.com/purge.git"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    cached_repo = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi" / "repos" / "purge-me"
    cached_repo.mkdir(parents=True)
    (cached_repo / "sentinel").write_text("cached\n", encoding="utf-8")

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "purge-me", "--purge"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not cached_repo.exists()


def test_ruyi_repo_error_cases(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: no active repo with id 'no-id'":
                "致命错误：没有 ID 为 'no-id' 的活动仓库",
            "fatal error: no repo with id 'no-id' found in user config":
                "致命错误：在用户配置中未找到 ID 为 'no-id' 的软件包仓库",
            "fatal error: a repo with id 'dup' already exists":
                "致命错误：已有一个 ID 为 'dup' 的软件包仓库了",
            "fatal error: invalid repo id 'bad id'": "致命错误：无效的仓库 ID 'bad id'",
            "fatal error: at least one of URL or --local must be provided":
                "致命错误：URL 或 --local 至少需要提供一个",
            "fatal error: local path 'relative/path' must be absolute":
                "致命错误：本地路径 'relative/path' 必须是绝对路径",
        },
    })
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(ruyi_exe, ["update", "--repo", "no-id"], env=isolated_env)
    try:
        child.expect_exact(_("fatal error: no active repo with id 'no-id'"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    for args in (
        ["repo", "remove", "no-id"],
        ["repo", "disable", "no-id"],
        ["repo", "enable", "no-id"],
        ["repo", "set-priority", "no-id", "20"],
    ):
        child = spawn_ruyi(ruyi_exe, args, env=isolated_env)
        try:
            child.expect_exact(_("fatal error: no repo with id 'no-id' found in user config"))
            child.expect(pexpect.EOF)
        finally:
            child.close()
        assert child.exitstatus == 1

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

    for args, message in (
        (["repo", "add", "bad id", "https://example.com/repo.git"],
         "fatal error: invalid repo id 'bad id'"),
        (["repo", "add", "no-source"],
         "fatal error: at least one of URL or --local must be provided"),
        (["repo", "add", "relative", "--local", "relative/path"],
         "fatal error: local path 'relative/path' must be absolute"),
    ):
        child = spawn_ruyi(ruyi_exe, args, env=isolated_env)
        try:
            child.expect_exact(_(message))
            child.expect(pexpect.EOF)
        finally:
            child.close()
        assert child.exitstatus == 1


def test_ruyi_repo_purge_preserves_external_local_path(
    ruyi_exe: str,
    ruyi_version: str,
    isolated_env: Dict[str, str],
    tmp_path: Path,
):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    external_repo = tmp_path / "external-local-repo"
    external_repo.mkdir()
    sentinel = external_repo / "sentinel"
    sentinel.write_text("must survive\n", encoding="utf-8")

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "add", "external-purge", "--local", str(external_repo)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["repo", "remove", "external-purge", "--purge"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["--porcelain", "repo", "list"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        records = [json.loads(line) for line in child.before.splitlines() if line]
    finally:
        child.close()
    assert child.exitstatus == 0
    assert all(record["id"] != "external-purge" for record in records)

    if not sentinel.exists():
        xfail_known_ruyi_defect(
            ruyi_version,
            ("0.50.0-beta.20260623", "0.51.0-alpha.20260616"),
            "repo remove --purge deletes an externally managed --local path",
        )
    assert sentinel.read_text(encoding="utf-8") == "must survive\n"
