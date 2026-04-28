import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


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
            "fatal error: atom gnu-upstream(>": "致命错误：atom gnu-upstream(>",
            ") matches no package in the repository": ") 在仓库中未匹配到任何软件包",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    failed_env = isolated_env.copy()
    failed_env["http_proxy"] = "http://0.0.0.0"
    failed_env["https_proxy"] = "http://0.0.0.0"
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
    assert (installed / "bin").exists()
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