import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_self_clean(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "info: removing all telemetry data": "信息：正在移除所有遥测数据",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(ruyi_exe, ["self", "clean"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    telemetry_dir = Path(isolated_env["XDG_STATE_HOME"]) / "ruyi" / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    payload = telemetry_dir / "payload.json"
    payload.write_text("{}", encoding="utf-8")

    child = spawn_ruyi(ruyi_exe, ["self", "clean", "--telemetry"], env=isolated_env)
    try:
        child.expect_exact(_("info: removing all telemetry data"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not telemetry_dir.exists()

    distfiles_dir = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi" / "distfiles"
    installed_dir = Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "binaries"
    distfiles_dir.mkdir(parents=True, exist_ok=True)
    installed_dir.mkdir(parents=True, exist_ok=True)
    (distfiles_dir / "test-distfile").write_text("distfile", encoding="utf-8")
    (installed_dir / "test-package").write_text("package", encoding="utf-8")

    child = spawn_ruyi(ruyi_exe, ["self", "clean", "--all", "--quiet"], env=isolated_env)
    try:
        while True:
            idx = child.expect([r"\(y/N\) ", pexpect.EOF])
            if idx == 1:
                break
            child.sendline("n")
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not distfiles_dir.exists()
    assert not installed_dir.exists()


def test_ruyi_self_clean_selectors(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "info: removing installed packages": "信息：正在移除已安装的软件包",
            "info: removing read status of news items": "信息：正在移除新闻条目的阅读状态",
            "info: removing downloaded distfiles": "信息：正在移除已下载的分发文件",
            "info: clearing the Ruyi program cache": "信息：正在清除 Ruyi 程序缓存",
            "info: removing the Ruyi repo": "信息：正在移除 Ruyi 仓库",
            "warn: not removing the Ruyi repo: it is outside of the Ruyi cache directory":
                "警告：不移除 Ruyi 仓库：它位于 Ruyi 缓存目录之外",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    cache_root = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi"
    data_root = Path(isolated_env["XDG_DATA_HOME"]) / "ruyi"
    state_root = Path(isolated_env["XDG_STATE_HOME"]) / "ruyi"
    distfiles_dir = cache_root / "distfiles"
    progcache_dir = cache_root / "progcache"
    installed_dir = data_root / "binaries"
    news_status = state_root / "news.read.txt"

    for path in (distfiles_dir, progcache_dir, installed_dir):
        path.mkdir(parents=True, exist_ok=True)
        (path / "sentinel").write_text("keep track\n", encoding="utf-8")
    news_status.parent.mkdir(parents=True, exist_ok=True)
    news_status.write_text("2024-01-14-ruyi-news\n", encoding="utf-8")

    for option, message, removed, preserved in (
        ("--distfiles", "info: removing downloaded distfiles", distfiles_dir, progcache_dir),
        ("--progcache", "info: clearing the Ruyi program cache", progcache_dir, installed_dir),
        ("--news-read-status", "info: removing read status of news items", news_status, installed_dir),
    ):
        child = spawn_ruyi(ruyi_exe, ["self", "clean", option], env=isolated_env)
        try:
            child.expect_exact(_(message))
            child.expect(pexpect.EOF)
        finally:
            child.close()
        assert child.exitstatus == 0
        assert not removed.exists()
        assert preserved.exists()

    repo_dirs = [cache_root / "repos" / "ruyisdk", cache_root / "packages-index"]
    managed_repo = next(path for path in repo_dirs if path.exists())
    child = spawn_ruyi(ruyi_exe, ["self", "clean", "--repo"], env=isolated_env)
    try:
        child.expect_exact(_("info: removing the Ruyi repo"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not managed_repo.exists()
    assert installed_dir.exists()

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--installed-pkgs", "--quiet"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        assert child.before == ""
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not data_root.exists()

    external_repo = tmp_path / "external-repo"
    external_repo.mkdir()
    sentinel = external_repo / "sentinel"
    sentinel.write_text("must survive\n", encoding="utf-8")
    child = spawn_ruyi(
        ruyi_exe,
        ["config", "set", "repo.local", str(external_repo)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["self", "clean", "--repo"], env=isolated_env)
    try:
        child.expect_exact(_("warn: not removing the Ruyi repo: it is outside of the Ruyi cache directory"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert sentinel.read_text(encoding="utf-8") == "must survive\n"


def test_ruyi_self_uninstall_safe_paths_do_not_remove_ruyi(
    ruyi_exe: str,
    isolated_env: Dict[str, str],
):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Continue": "继续",
            "cannot be uninstalled": "不能以这种方式卸载",
            "info: aborting uninstallation": "信息：中止卸载",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    ruyi_path = Path(ruyi_exe)

    data_sentinel = Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "sentinel"
    cache_sentinel = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi" / "sentinel"
    state_sentinel = Path(isolated_env["XDG_STATE_HOME"]) / "ruyi" / "sentinel"
    for sentinel in (data_sentinel, cache_sentinel, state_sentinel):
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("must survive\n", encoding="utf-8")

    for args in (["self", "uninstall"], ["self", "uninstall", "--purge"]):
        child = spawn_ruyi(ruyi_exe, args, env=isolated_env)
        try:
            idx = child.expect_exact([_("Continue"), _("cannot be uninstalled")])
            if idx == 1:
                child.expect(pexpect.EOF)
            else:
                child.expect(r"\(y/N\) ")
                child.sendline("n")
                child.expect_exact(_("info: aborting uninstallation"))
                child.expect(pexpect.EOF)
        finally:
            child.close()
        if idx == 1:
            assert child.exitstatus == 1
        else:
            assert child.exitstatus == 0
        assert ruyi_path.exists()
        assert data_sentinel.exists()
        assert cache_sentinel.exists()
        assert state_sentinel.exists()

    child = spawn_ruyi(ruyi_exe, ["version"], env=isolated_env)
    try:
        child.expect_exact("Ruyi ")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
