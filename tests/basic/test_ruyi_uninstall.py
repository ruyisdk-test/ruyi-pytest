
import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_uninstall(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    """测试 `ruyi uninstall` 命令：不存在包、交互式取消/确认、已卸载包重复卸载。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: atom ": "致命错误：atom ",
            " is non-existent or not installed": " 不存在或未安装",
            r"info: downloading .*": r"信息：正在将 http.* 下载到 .*",
            r"info: extracting .* for package gnu-upstream-(\S+)": r"信息：正在为软件包 gnu-upstream-(\S+) 解压缩 ",
            r"info: package .* installed to (\S+)": r"信息：软件包 .* 已安装到 (\S+)",
            "info: the following packages will be uninstalled:": "信息：以下软件包将被卸载：",
            "info: uninstalling package ": "信息：正在卸载软件包 ",
            "info: package ": "信息：软件包 ",
            " uninstalled": " 已被卸载",
            "Proceed?": "继续吗？",
            "List of available packages:": "可用软件包列表：",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # -------- uninstall non-existent package --------
    child = spawn_ruyi(
        ruyi_exe,
        ["uninstall", "nonexistent-pkg-foo"],
        env=isolated_env,
    )
    try:
        child.expect_exact(
            _("fatal error: atom ") + "nonexistent-pkg-foo" +
            _(" is non-existent or not installed")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # -------- uninstall a known but not-installed package --------
    child = spawn_ruyi(
        ruyi_exe,
        ["uninstall", "coremark"],
        env=isolated_env,
    )
    try:
        child.expect_exact(
            _("fatal error: atom ") + "coremark" +
            _(" is non-existent or not installed")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # -------- install a package first --------
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "gnu-upstream"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect(_(r"info: downloading .*"))
        child.expect(_(r"info: extracting .* for package gnu-upstream-(\S+)"))
        installed_ver = child.match.group(1)
        child.expect(_(r"info: package .* installed to (\S+)"))
        install_dir = child.match.group(1)
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert Path(install_dir).exists()

    # -------- confirm via ruyi list that package shows as installed --------
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-upstream", "--is-installed", "y"],
        env=isolated_env,
    )
    try:
        child.expect_exact("toolchain/gnu-upstream")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # -------- uninstall interactively (abort) --------
    child = spawn_ruyi(
        ruyi_exe,
        ["uninstall", "gnu-upstream"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: the following packages will be uninstalled:"))
        child.expect(_("Proceed?") + r" \(y/N\) ")
        child.sendline("n")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # package should still be installed after abort
    assert Path(install_dir).exists()

    # -------- uninstall interactively (confirm) --------
    child = spawn_ruyi(
        ruyi_exe,
        ["uninstall", "gnu-upstream"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: the following packages will be uninstalled:"))
        child.expect(_("Proceed?") + r" \(y/N\) ")
        child.sendline("y")
        child.expect(_("info: uninstalling package ") + r".*gnu-upstream")
        child.expect(_("info: package ") + r".*gnu-upstream.*" + _(" uninstalled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # verify the installed directory was removed
    assert not Path(install_dir).exists()

    # -------- confirm via ruyi list that package no longer shows as installed --------
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-upstream", "--is-installed", "y"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect(pexpect.EOF)
        after = child.before
        assert "toolchain/gnu-upstream" not in after
    finally:
        child.close()
    assert child.exitstatus == 0

    # -------- uninstall an already-uninstalled package --------
    child = spawn_ruyi(
        ruyi_exe,
        ["uninstall", "gnu-upstream"],
        env=isolated_env,
    )
    try:
        child.expect_exact(
            _("fatal error: atom ") + "gnu-upstream" +
            _(" is non-existent or not installed")
        )
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1


def test_ruyi_uninstall_assume_yes(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    """测试 `ruyi uninstall -y` 及 `remove`/`rm` 别名非交互式卸载。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            r"info: downloading .*": r"信息：正在将 http.* 下载到 .*",
            r"info: extracting .* for package gnu-upstream-(\S+)": r"信息：正在为软件包 gnu-upstream-(\S+) 解压缩 ",
            r"info: package .* installed to (\S+)": r"信息：软件包 .* 已安装到 (\S+)",
            "info: the following packages will be uninstalled:": "信息：以下软件包将被卸载：",
            "info: uninstalling package ": "信息：正在卸载软件包 ",
            "info: package ": "信息：软件包 ",
            " uninstalled": " 已被卸载",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # install a package
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "gnu-upstream"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect(_(r"info: downloading .*"))
        child.expect(_(r"info: extracting .* for package gnu-upstream-(\S+)"))
        child.expect(_(r"info: package .* installed to (\S+)"))
        install_dir = child.match.group(1)
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert Path(install_dir).exists()

    # uninstall with -y (should skip the Proceed? prompt)
    child = spawn_ruyi(
        ruyi_exe,
        ["uninstall", "-y", "gnu-upstream"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: the following packages will be uninstalled:"))
        child.expect(_("info: uninstalling package ") + r".*gnu-upstream")
        child.expect(_("info: package ") + r".*gnu-upstream.*" + _(" uninstalled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # verify the installed directory was removed
    assert not Path(install_dir).exists()

    # install again for "remove" alias testing
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "gnu-upstream"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect(_(r"info: extracting .* for package gnu-upstream-(\S+)"))
        child.expect(_(r"info: package .* installed to (\S+)"))
        install_dir = child.match.group(1)
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # uninstall via "remove" alias with -y
    child = spawn_ruyi(
        ruyi_exe,
        ["remove", "-y", "gnu-upstream"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: the following packages will be uninstalled:"))
        child.expect(_("info: uninstalling package ") + r".*gnu-upstream")
        child.expect(_("info: package ") + r".*gnu-upstream.*" + _(" uninstalled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not Path(install_dir).exists()

    # install again for "rm" alias testing
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "gnu-upstream"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect(_(r"info: extracting .* for package gnu-upstream-(\S+)"))
        child.expect(_(r"info: package .* installed to (\S+)"))
        install_dir = child.match.group(1)
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # uninstall via "rm" alias with -y
    child = spawn_ruyi(
        ruyi_exe,
        ["rm", "-y", "gnu-upstream"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: the following packages will be uninstalled:"))
        child.expect(_("info: uninstalling package ") + r".*gnu-upstream")
        child.expect(_("info: package ") + r".*gnu-upstream.*" + _(" uninstalled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not Path(install_dir).exists()
