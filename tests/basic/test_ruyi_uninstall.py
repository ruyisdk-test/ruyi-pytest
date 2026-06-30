
import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_uninstall(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    """Test `ruyi uninstall` command: nonexistent package, interactive cancel/confirm, re-uninstall already removed package."""
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

    # Uninstall a nonexistent package
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

    # Uninstall a known but not installed package
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

    # Install a package first
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

    # Verify package shows as installed via ruyi list
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

    # Interactive uninstall (cancel)
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

    # Package should still exist after cancellation
    assert Path(install_dir).exists()

    # Interactive uninstall (confirm)
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

    # Verify install directory was deleted
    assert not Path(install_dir).exists()

    # Verify package no longer shows as installed via ruyi list
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

    # Uninstall an already uninstalled package
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
    """Test `ruyi uninstall -y` and `remove`/`rm` aliases for non-interactive uninstall."""
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

    # Install a package
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

    # Uninstall with -y (skip confirmation prompt)
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

    # Verify install directory was deleted
    assert not Path(install_dir).exists()

    # Reinstall to test "remove" alias
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

    # Uninstall via "remove" alias with -y
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

    # Reinstall to test "rm" alias
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

    # Uninstall via "rm" alias with -y
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
