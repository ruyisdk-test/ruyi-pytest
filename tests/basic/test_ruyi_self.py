import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import (
    bind_gettext,
    spawn_ruyi,
    spawn_ruyi_to_eof,
    ruyi_init_default_telemetry,
    ruyi_install,
)


def test_ruyi_self_clean(
    ruyi_exe: str,
    ruyi_dep: bool,
    isolated_env: Dict[str, str],
    tmp_path: Path,
):
    """Exercise each individual cleanup selector in one usage environment."""
    gettext = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "info: removing read status of news items": "信息：正在移除新闻条目的阅读状态",
            "info: removing downloaded distfiles": "信息：正在移除已下载的分发文件",
            "info: clearing the Ruyi program cache": "信息：正在清除 Ruyi 程序缓存",
            "info: removing installed packages": "信息：正在移除已安装的软件包",
            "info: removing state data": "信息：正在移除状态数据",
            "info: removing cached data": "信息：正在移除缓存数据",
            "info: removing the Ruyi repo": "信息：正在移除 Ruyi 仓库",
            "info: removing all telemetry data": "信息：正在移除所有遥测数据",
        },
    })
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    status = spawn_ruyi_to_eof(ruyi_exe, ["news", "read", "-q"], isolated_env)
    assert status == 0
    news_read_status_file = (
        Path(isolated_env["XDG_STATE_HOME"]) / "ruyi" / "news.read.txt"
    )
    assert news_read_status_file.is_file()

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--news-read-status"],
        isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before or ""
    finally:
        child.close()
    status = child.exitstatus
    assert status == 0
    assert gettext("info: removing read status of news items") in output
    assert not news_read_status_file.exists()

    # Install one package to create command-generated distfile and package state.
    ruyi_install(ruyi_exe, ["board-util/wlink"], isolated_env)
    cache_root = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi"
    data_root = Path(isolated_env["XDG_DATA_HOME"]) / "ruyi"
    distfiles_dir = cache_root / "distfiles"
    distfiles_before = list(distfiles_dir.iterdir())
    assert distfiles_before
    assert any(path.is_file() for path in data_root.rglob("*"))

    # Python/package installations do not naturally create this cache.
    progcache_dir = cache_root / "progcache"
    progcache_dir.mkdir(parents=True, exist_ok=True)
    progcache_sentinel = progcache_dir / "sentinel"
    progcache_sentinel.write_text("keep until progcache cleanup\n", encoding="utf-8")

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--distfiles"],
        isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before or ""
    finally:
        child.close()
    status = child.exitstatus
    assert status == 0
    assert gettext("info: removing downloaded distfiles") in output
    assert all(not path.exists() for path in distfiles_before)
    assert progcache_sentinel.exists()

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--progcache"],
        isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before or ""
    finally:
        child.close()
    status = child.exitstatus
    assert status == 0
    assert gettext("info: clearing the Ruyi program cache") in output
    assert not progcache_dir.exists()
    assert data_root.exists()

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--installed-pkgs"],
        isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before or ""
    finally:
        child.close()
    status = child.exitstatus
    assert status == 0
    assert gettext("info: removing installed packages") in output
    assert not data_root.exists()

    repo_candidates = [cache_root / "repos" / "ruyisdk", cache_root / "packages-index"]
    managed_repo = next(path for path in repo_candidates if path.exists())
    keep_sentinel = cache_root / "keep-sentinel"
    keep_sentinel.write_text("must survive repo cleanup\n", encoding="utf-8")
    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--repo"],
        isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before or ""
    finally:
        child.close()
    status = child.exitstatus
    assert status == 0
    assert gettext("info: removing the Ruyi repo") in output
    assert not managed_repo.exists()
    assert keep_sentinel.exists()

    # Clear telemetry before recreating Ruyi state for the aggregate cleanup.
    telemetry_dir = Path(isolated_env["XDG_STATE_HOME"]) / "ruyi" / "telemetry"
    if not any(telemetry_dir.rglob("*")):
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        (telemetry_dir / "sentinel").write_text("telemetry cleanup\n", encoding="utf-8")
    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--telemetry"],
        isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before or ""
    finally:
        child.close()
    status = child.exitstatus
    assert status == 0
    assert gettext("info: removing all telemetry data") in output
    assert not any(telemetry_dir.rglob("*"))

    # Recreate real Ruyi state for the aggregate cleanup, which runs last.
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    state_root = Path(isolated_env["XDG_STATE_HOME"]) / "ruyi"
    ruyi_install(ruyi_exe, ["board-util/wlink"], isolated_env)
    external_sentinel = tmp_path / "external-sentinel"
    external_sentinel.write_text("must survive\n", encoding="utf-8")

    assert data_root.exists()
    assert state_root.exists()
    assert cache_root.exists()
    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--all"],
        isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before or ""
    finally:
        child.close()
    status = child.exitstatus
    assert status == 0
    assert gettext("info: removing installed packages") in output
    assert gettext("info: removing state data") in output
    assert gettext("info: removing cached data") in output
    assert not data_root.exists()
    assert not state_root.exists()
    assert not cache_root.exists()
    assert external_sentinel.read_text(encoding="utf-8") == "must survive\n"


def test_ruyi_self_uninstall(
    standalone_exe,
    standalone_env: Dict[str, str],
    tmp_path: Path,
):
    """Delete only temporary same-version standalone copies."""
    gettext = bind_gettext(standalone_env, {
        "zh_CN.UTF-8": {
            "info: uninstallation consent given over CLI, proceeding": "信息：已通过 CLI 同意卸载，继续进行",
            "info: ruyi is uninstalled": "信息：ruyi 已被卸载",
            "info: removing installed packages": "信息：正在移除已安装的软件包",
            "info: removing state data": "信息：正在移除状态数据",
            "info: removing cached data": "信息：正在移除缓存数据",
        },
    })
    external_sentinel = tmp_path / "outside-xdg-sentinel"
    external_sentinel.write_text("must survive uninstall\n", encoding="utf-8")

    for label, extra_args in (("normal", []), ("purge", ["--purge"])):
        executable = standalone_exe(label)
        data_root = Path(standalone_env["XDG_DATA_HOME"]) / "ruyi"
        state_root = Path(standalone_env["XDG_STATE_HOME"]) / "ruyi"
        cache_root = Path(standalone_env["XDG_CACHE_HOME"]) / "ruyi"
        for root in (data_root, state_root, cache_root):
            root.mkdir(parents=True, exist_ok=True)
            (root / f"{label}-sentinel").write_text("must survive\n", encoding="utf-8")

        removed_by_uninstall = False
        try:
            child = spawn_ruyi(
                str(executable),
                ["self", "uninstall", "-y", *extra_args],
                standalone_env,
            )
            try:
                child.expect(pexpect.EOF)
                output = child.before or ""
            finally:
                child.close()
            status = child.exitstatus
            assert status == 0, output
            assert gettext("info: uninstallation consent given over CLI, proceeding") in output
            assert gettext("info: ruyi is uninstalled") in output
            removed_by_uninstall = not executable.exists()
        finally:
            executable.unlink(missing_ok=True)
        assert removed_by_uninstall, (
            f"self uninstall did not remove temporary executable: {executable}; "
            f"output={output!r}"
        )

        if extra_args:
            assert gettext("info: removing installed packages") in output
            assert gettext("info: removing state data") in output
            assert gettext("info: removing cached data") in output
            assert not data_root.exists()
            assert not state_root.exists()
            assert not cache_root.exists()
        else:
            assert (data_root / "normal-sentinel").exists()
            assert (state_root / "normal-sentinel").exists()
            assert (cache_root / "normal-sentinel").exists()

        assert external_sentinel.read_text(encoding="utf-8") == (
            "must survive uninstall\n"
        )
