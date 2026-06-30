
import os
import pexpect
import shutil
import stat

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def test_ruyi_self_clean(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Cleaned news read status": "已清理新闻已读状态",
            "Cleaned distfiles": "已清理分发文件",
            r"Cleaned telemetry data\.?": r"已清理遥测数据。?",
            "nothing to clean": "没有需要清理的内容",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi self clean（无参数 → 退出码 1）
    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # ruyi self clean --news-read-status
    # 已读状态记录在 XDG_STATE_HOME/ruyi/news.read.txt（每行一条新闻 ID）
    # 先读一条新闻让 ruyi 自己写出该文件，再验证 clean 把它删掉
    news_read_status_file = Path(isolated_env["XDG_STATE_HOME"]) / "ruyi" / "news.read.txt"
    assert not news_read_status_file.exists()  # 初始：没有任何已读记录

    child = spawn_ruyi(
        ruyi_exe,
        ["news", "read", "-q"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    # 确认 ruyi 确实写出了已读状态文件且非空
    assert news_read_status_file.exists()
    assert news_read_status_file.stat().st_size > 0

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--news-read-status"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    # 验证已读状态文件确实被删除
    assert not news_read_status_file.exists()

    # ruyi self clean --distfiles
    # 先安装一个小包，产生真实的下载文件记录
    # gnu-plct-xthead 足够小，不会让测试耗时太长
    ruyi_install(ruyi_exe, ["gnu-plct-xthead"], isolated_env)

    # 验证安装后 distfiles 目录有真实下载的文件
    distfiles_dir = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi" / "distfiles"
    assert distfiles_dir.exists()
    distfiles_before = list(distfiles_dir.iterdir())
    assert len(distfiles_before) > 0

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--distfiles"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    # 验证之前下载的分发文件确实被清理了
    for f in distfiles_before:
        assert not f.exists()

    # ruyi self clean --installed-pkgs
    # 上面的 ruyi_install 除了下载 distfile，还把包装到了 XDG_DATA_HOME/ruyi/
    # --distfiles 只删了缓存里的安装包，已安装的包仍在 data_root 下
    data_root = Path(isolated_env["XDG_DATA_HOME"]) / "ruyi"
    assert data_root.exists()
    installed_before = [p for p in data_root.rglob("*") if p.is_file()]
    assert len(installed_before) > 0

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--installed-pkgs"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    # 验证整个 data_root 被删除
    assert not data_root.exists()

    # ruyi self clean --progcache
    # progcache 仅独立二进制形态的 ruyi 才会产生；pip/uv 安装不会，此时目录不存在
    progcache_dir = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi" / "progcache"
    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--progcache"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    # 无论之前是否存在（取决于 ruyi 安装形态），清理后都不应存在
    assert not progcache_dir.exists()

    # ruyi self clean --telemetry
    # 遥测在默认 local 模式下就会记录数据：前面的 update 和 install 调用
    # 已经在 XDG_STATE_HOME/ruyi/telemetry/ 下写入了 installation.json 和 raw 事件
    telemetry_dir = Path(isolated_env["XDG_STATE_HOME"]) / "ruyi" / "telemetry"
    assert telemetry_dir.exists()
    telemetry_before = [p for p in telemetry_dir.rglob("*") if p.is_file()]
    assert len(telemetry_before) > 0

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--telemetry"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    # 验证之前记录的遥测数据确实被清理
    assert not telemetry_dir.exists() or not any(p.is_file() for p in telemetry_dir.rglob("*"))

    # ruyi self clean --repo
    # 仓库克隆在 XDG_CACHE_HOME/ruyi/repos/ 下（含 .git）
    # 放在最后测，因为删掉仓库后依赖仓库的命令（news/list/install）都无法工作
    repos_root = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi" / "repos"
    assert repos_root.exists()
    git_dirs_before = list(repos_root.rglob(".git"))
    assert len(git_dirs_before) > 0

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--repo"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    # 验证仓库确实被删除
    git_dirs_after = list(repos_root.rglob(".git"))
    assert len(git_dirs_after) == 0

    # ruyi self clean --quiet
    # --quiet 不删除任何东西，只抑制输出；需要先重新 init 产生一点可清理的数据
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    # 读一条新闻产生已读记录，给 --quiet 一个可清理的目标
    child = spawn_ruyi(
        ruyi_exe,
        ["news", "read", "-q"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--quiet", "--news-read-status"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        quiet_output = child.before or ""
    finally:
        child.close()
    assert child.exitstatus == 0
    # --quiet 不应输出任何 info: 状态行
    assert "info:" not in quiet_output
    # 同时验证清理本身仍然生效
    assert not news_read_status_file.exists()

    # ruyi self clean --all
    # --all 会删除 data_root + state_root + cache_root
    data_root = Path(isolated_env["XDG_DATA_HOME"]) / "ruyi"
    state_root = Path(isolated_env["XDG_STATE_HOME"]) / "ruyi"
    cache_root = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi"
    # 上面的重新 init 会在 cache_root/state_root 下重建仓库、遥测等数据
    assert cache_root.exists() or state_root.exists()

    child = spawn_ruyi(
        ruyi_exe,
        ["self", "clean", "--all"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    # 验证三个根目录全部被删除
    assert not data_root.exists()
    assert not state_root.exists()
    assert not cache_root.exists()


def test_ruyi_self_uninstall(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "this ruyi is not in standalone form, and cannot be uninstalled this way": "不是独立形式",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi self uninstall
    # 非独立安装（如 pip install）直接报错退出，不会出现交互式提示
    child = spawn_ruyi(
        ruyi_exe,
        ["self", "uninstall"],
        env=isolated_env,
    )
    try:
        idx = child.expect([r"\(y/N\)", _("this ruyi is not in standalone form, and cannot be uninstalled this way"), pexpect.EOF])
        if idx == 0:
            # 独立安装：测试取消卸载
            child.sendline("n")
            child.expect(pexpect.EOF)
            child.wait()
            assert child.exitstatus == 0
            assert Path(isolated_env["XDG_CONFIG_HOME"]).exists()

            # 独立安装：测试确认卸载
            # 先检查对 ruyi 二进制所在目录是否有写入权限（无权限时如 CI 环境跳过）
            ruyi_exe_path = Path(ruyi_exe).resolve()
            if not os.access(ruyi_exe_path.parent, os.W_OK):
                # 无法删除/恢复 ruyi 二进制，跳过确认卸载测试
                return

            backup_path = Path(isolated_env["HOME"]) / (ruyi_exe_path.name + ".backup")
            shutil.copy2(ruyi_exe, backup_path)
            try:
                child2 = spawn_ruyi(
                    ruyi_exe,
                    ["self", "uninstall"],
                    env=isolated_env,
                )
                try:
                    child2.expect(r"\(y/N\)")
                    child2.sendline("y")
                    child2.expect(pexpect.EOF)
                    child2.wait()
                finally:
                    child2.close()
                assert child2.exitstatus == 0
            finally:
                # 恢复 ruyi 二进制
                shutil.copy2(backup_path, ruyi_exe)
                os.chmod(ruyi_exe, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                backup_path.unlink()
        else:
            # 非独立安装：直接报错退出
            child.expect(pexpect.EOF)
            child.wait()
            assert child.exitstatus != 0
    finally:
        child.close()
