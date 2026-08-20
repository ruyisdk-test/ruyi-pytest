
import hashlib
import platform
import pexpect
import pytest
import time
import urllib.request

from pathlib import Path
from typing import Dict

from tests.helpers import (
    bind_gettext,
    env_with_blocked_network,
    ruyi_init_default_telemetry,
    spawn_ruyi,
    xfail_known_ruyi_defect,
)


def test_ruyi_install(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            r"info: downloading .*": r"信息：正在将 http.* 下载到 .*",
            "warn: failed to fetch distfile: command ": "警告：获取分发文件失败：命令 ",
            "info: retrying download (2 of 3 times)": "信息：正在重试下载（第 2 次，共 3 次）",
            "info: retrying download (3 of 3 times)": "信息：正在重试下载（第 3 次，共 3 次）",
            "fatal error: failed to fetch ": "致命错误：获取 ",
            "Downloads can fail for a multitude of reasons": "下载可能因各种原因失败，",
            "* Basic connectivity problems": "* 基本连接问题",
            r"info: extracting .* for package gnu-upstream-(\S+)": r"信息：正在为软件包 gnu-upstream-(\S+) 解压缩 ",
            r"info: package .* installed to (\S+)": r"信息：软件包 .* 已安装到 (\S+)",
            "info: skipping already installed package": "信息：跳过已安装的软件包 ",
            r"warn: package gnu-upstream-\S+ seems already installed; purging and re-installing due to --reinstall":
                r"警告：软件包 gnu-upstream-\S+ 似乎已安装；由于传入了 --reinstall，将移除并重新安装它",
            "fatal error: atom gnu-upstream(>": "致命错误：atom gnu-upstream(>",
            ") matches no package in the repository": ") 在仓库中未匹配到任何软件包",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    failed_env = env_with_blocked_network(isolated_env)
    # ruyi install with proxy
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "gnu-upstream"],
        env=failed_env,
        timeout=10 * 60,
    )
    try:
        child.expect(_(r"info: downloading .*"))
        child.expect_exact(_("warn: failed to fetch distfile: command "))
        child.expect_exact(_("info: retrying download (2 of 3 times)"))
        child.expect_exact(_("warn: failed to fetch distfile: command "))
        child.expect_exact(_("info: retrying download (3 of 3 times)"))
        child.expect_exact(_("warn: failed to fetch distfile: command "))
        child.expect_exact(_("fatal error: failed to fetch "))
        child.expect_exact(_("Downloads can fail for a multitude of reasons"))
        child.expect_exact(_("* Basic connectivity problems"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1

    # ruyi install gnu-upstream
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
        installed = Path(child.match.group(1))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
    assert installed.exists()
    binary_root = Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "binaries"
    assert installed.resolve().is_relative_to(binary_root.resolve())

    sentinel = installed / "reinstall-sentinel"
    sentinel.write_text("remove me\n", encoding="utf-8")
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "--reinstall", "gnu-upstream"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect(_(r"warn: package gnu-upstream-\S+ seems already installed; purging and re-installing due to --reinstall"))
        child.expect(_(r"info: package .* installed to (\S+)"))
        reinstalled = Path(child.match.group(1))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert reinstalled == installed
    assert reinstalled.exists()
    assert (reinstalled / "bin").exists()
    assert not sentinel.exists()
    assert (installed / "toolchain.cmake").exists()

    # again: ruyi install gnu-upstream
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "gnu-upstream"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: skipping already installed package"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # again: ruyi install name:gnu-upstream
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "name:gnu-upstream"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect_exact(_("info: skipping already installed package"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # again: ruyi install 'gnu-upstream(0.20260201.0)'
    child = spawn_ruyi(
        ruyi_exe,
        ["install", f"gnu-upstream({installed_ver})"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect_exact(_("info: skipping already installed package"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # again: ruyi install 'gnu-upstream(==0.20260201.0)'
    child = spawn_ruyi(
        ruyi_exe,
        ["install", f"gnu-upstream(=={installed_ver})"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect_exact(_("info: skipping already installed package"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi install 'gnu-upstream(>0.20260201.0)'
    child = spawn_ruyi(
        ruyi_exe,
        ["install", f"gnu-upstream(>{installed_ver})"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect_exact(_("fatal error: atom gnu-upstream(>") + installed_ver +
                           _(") matches no package in the repository"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1


def test_ruyi_install_fetch_reinstall_and_alias(
    ruyi_exe: str,
    ruyi_dep: bool,
    isolated_env: Dict[str, str],
    tmp_path: Path,
):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            r"info: downloading .*": r"信息：正在将 http.* 下载到 .*",
            "fatal error: don't know how to handle non-binary package ruyisdk-demo":
                "致命错误：不知道如何处理非二进制软件包 ruyisdk-demo",
            r"info: extracting .* for package gnu-upstream-(\S+)": r"信息：正在为软件包 gnu-upstream-(\S+) 解压缩 ",
            r"info: package .* installed to (\S+)": r"信息：软件包 .* 已安装到 (\S+)",
            "info: skipping already installed package": "信息：跳过已安装的软件包 ",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["install", "-f", "ruyisdk-demo"],
        env=isolated_env,
        timeout=10 * 60,
        cwd=str(tmp_path),
    )
    try:
        child.expect(_(r"info: downloading .*"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not (Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "binaries").exists()

    child = spawn_ruyi(
        ruyi_exe,
        ["install", "--reinstall", "ruyisdk-demo"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: don't know how to handle non-binary package ruyisdk-demo"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 2

    child = spawn_ruyi(
        ruyi_exe,
        ["i", "gnu-upstream"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect(_(r"info: extracting .* for package gnu-upstream-(\S+)"))
        child.expect(_(r"info: package .* installed to (\S+)"))
        installed = Path(child.match.group(1))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert installed.exists()

    child = spawn_ruyi(
        ruyi_exe,
        ["install", "gnu-upstream", "gnu-upstream"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: skipping already installed package"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0


@pytest.mark.skipif(
    platform.machine() not in {"aarch64", "riscv64", "x86_64"},
    reason="board-util/wlink has no binary for this host",
)
def test_ruyi_install_binary_fetch_only_has_no_install_state(
    ruyi_exe: str,
    ruyi_version: str,
    ruyi_dep: bool,
    isolated_env: Dict[str, str],
):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["install", "--fetch-only", "board-util/wlink"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    binary_root = Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "binaries"
    install_roots = list(binary_root.glob("*/wlink-*")) if binary_root.exists() else []

    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "wlink", "--is-installed", "y"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        assert "board-util/wlink" not in child.before
    finally:
        child.close()
    assert child.exitstatus == 0
    if install_roots:
        assert all(path.is_dir() and not any(path.iterdir()) for path in install_roots)
        xfail_known_ruyi_defect(
            ruyi_version,
            ("0.50.0-beta.20260623", "0.51.0-alpha.20260616"),
            "binary install --fetch-only creates an empty installation root",
        )
    assert not install_roots


def test_ruyi_install_host(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "cannot be automatically fetched": "无法被自动获取",
            "info: instructions on fetching this file:": "信息：获取此文件的方法说明：",
            "Place the downloaded file at ": "将下载完成的文件置于 ",
            " and re-run the install command.": " 并重新执行安装命令。",
            r"info: extracting wps-office_\S+_amd64\.deb for package wps-office-\S+": r"信息：正在为软件包 wps-office-\S+ 解压缩 ",
            r"info: package wps-office-\S+ installed to \S+": r"信息：软件包 wps-office-\S+ 已安装到 \S+",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # install --host
    child = spawn_ruyi(
        ruyi_exe,
        ["install", "--host", "x86_64", "extra/wps-office"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("cannot be automatically fetched"))
        child.expect_exact(_("info: instructions on fetching this file:"))
        child.expect_exact("https://linux.wps.cn")
        child.expect_exact(_("Place the downloaded file at "))
        child.expect_exact(str((Path(isolated_env ["XDG_CACHE_HOME"]) / "ruyi" / "distfiles").absolute()))
        child.expect(r"wps-office_(\d+.\d+.\d+).(\d+)_amd64.deb")
        version = child.match.group(1)
        build = child.match.group(2)
        child.expect_exact(_(" and re-run the install command."))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus != 0

    #####
    # view-source:https://linux.wps.cn/#
    #
    # line 177
    #
    # <a href="#" onClick="downLoad('https://wps-linux-personal.wpscdn.cn/wps/download/ep/Linux2023/17900/wps-office_12.1.0.17900_amd64.deb','64位 Deb格式','For X64')" class="version_btn" style="width: 115px;padding-right: 10px;" >For X64</a>
    #
    # line 225
    #
    # <script>
    #     function downLoad(url,eventType,eventName){
    #         _czc.push(['_trackEvent', eventType, '点击', eventName]);
    #         _hmt.push(['_trackEvent', eventType, '点击', eventName]);
    #         var urlObj = new URL(url);
    #         var uri = urlObj.pathname;
    #         var secrityKey = "7f8faaaa468174dc1c9cd62e5f218a5b";
    #         var timestamp10 = Math.floor(new Date().getTime() / 1000);
    #         var md5hash = CryptoJS.MD5(secrityKey+uri+timestamp10);
    #         url += '?t='+timestamp10+'&k='+md5hash
    #
    #         var link = document.createElement('a')
    #       link.href = url
    #       link.style.display = 'none'
    #       document.body.appendChild(link)
    #       link.click()
    #       document.body.removeChild(link)
    #
    #
    #
    #     }
    # </script>
    #####

    file = f"wps-office_{version}.{build}_amd64.deb"
    url = f"https://wps-linux-personal.wpscdn.cn/wps/download/ep/Linux2023/{build}/{file}"
    uri = url.removeprefix("https://wps-linux-personal.wpscdn.cn")
    timestamp10 = str(int(time.time()))
    security_key = "7f8faaaa468174dc1c9cd62e5f218a5b"
    md5hash = hashlib.md5(f"{security_key}{uri}{timestamp10}".encode("utf-8")).hexdigest()
    url = f"{url}?t={timestamp10}&k={md5hash}"

    distfiles_dir = Path(isolated_env["XDG_CACHE_HOME"]) / "ruyi" / "distfiles"
    distfiles_dir.mkdir(parents=True, exist_ok=True)
    dest = distfiles_dir / file
    urllib.request.urlretrieve(url, dest)

    child = spawn_ruyi(
        ruyi_exe,
        ["install", "--host", "x86_64", "extra/wps-office"],
        env=isolated_env,
        timeout=10 * 60,
    )
    try:
        child.expect(_(r"info: extracting wps-office_\S+_amd64\.deb for package wps-office-\S+"))
        child.expect(_(r"info: package wps-office-\S+ installed to \S+"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
