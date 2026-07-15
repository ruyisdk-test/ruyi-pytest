
import json
import pexpect
import platform
import pytest
import re

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def test_ruyi_list(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "List of available packages:": "可用软件包列表：",
            "(latest)": "(最新)",
            "prerelease": "预发布",
            "latest-prerelease": "最新预发布",
            "Package declares": "软件包声明了",
            "distfile(s):": "个分发文件：",
            "* Slug: (none)": "* Slug：（无）",
            "* Package kind: [": "* 软件包类型：[",
            "* Vendor: PLCT": "* 供应商：PLCT",
            "* Upstream version number:": "* 上游版本号：",
            "### Binary artifacts": "### 二进制制品",
            "### Toolchain metadata": "### 工具链元数据",
            "* Target:": "* 目标：",
            "* Quirks:": "* 特殊特性：",
            "* Components:": "* 组件：",
            "installed": "已安装",
            "arch:": "架构：",
            "needs quirks:": "需要特殊特性：",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi list --name-contains ""
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", ""],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("* toolchain")
        child.expect_exact(_("(latest)"))
        between = child.before
        assert _("Package declares") not in between
        child.expect(pexpect.EOF)
        after = child.before
        assert _("Package declares") not in after
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains coremark
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "coremark"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("* source/coremark")
        child.expect_exact(_("prerelease"))
        child.expect_exact(_("latest-prerelease"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains "gnu-plct-xthead" --verbose
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-plct-xthead", "--verbose"],
        env=isolated_env,
    )
    try:
        child.expect(r"## toolchain/gnu-plct-xthead .*")
        child.expect_exact(_("* Slug: (none)"))
        child.expect_exact(_("* Package kind: ["))
        child.expect_exact(_("* Vendor: PLCT"))
        child.expect_exact(_("* Upstream version number:"))
        child.expect(
            rf"{re.escape(_('Package declares'))} \d+ {re.escape(_('distfile(s):'))}"
        )
        child.expect_exact(_("### Binary artifacts"))
        child.expect_exact(_("### Toolchain metadata"))
        child.expect_exact(_("* Target:"))
        child.expect_exact(_("* Quirks:"))
        child.expect_exact(_("* Components:"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains 'gnu-plct-xthead' --is-installed y
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-plct-xthead", "--is-installed", "y"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect(pexpect.EOF)
        after = child.before
        assert _("installed") not in after
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains 'gnu-plct-xthead' --is-installed n
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-plct-xthead", "--is-installed", "n"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("toolchain/gnu-plct-xthead")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi install gnu-plct-xthead
    ruyi_install(ruyi_exe, ["gnu-plct-xthead"], env=isolated_env)

    # ruyi list --name-contains 'gnu-plct-xthead' --is-installed y
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-plct-xthead", "--is-installed", "y"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact(_("installed"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains 'gnu-plct-xthead' --is-installed n
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-plct-xthead", "--is-installed", "n"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect(pexpect.EOF)
        after = child.before
        assert "toolchain/gnu-plct-xthead" not in after
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --category-is source
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--category-is", "source"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("source/coremark")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --category-contains sourc
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--category-contains", "sourc"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("source/coremark")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list profiles
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "profiles"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("arch:"))
        child.expect_exact(_("needs quirks:"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0


def test_ruyi_list_unavailable_pkg(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "List of available packages:": "可用软件包列表：",
            "latest": "最新",
            "no binary for current host": "无适用当前主机的二进制文件",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    if platform.machine() == "x86_64":
        pkg = "box64"
    else:
        pkg = "wps-office"

    # ruyi list --name-contains pkg
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", pkg],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact(_("latest"))
        child.expect_exact(_("no binary for current host"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0


def test_ruyi_list_contract_and_porcelain(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: no filter specified for list operation":
                "致命错误：未为 list 操作指定过滤器",
            "info: for the old behavior of listing all packages, try ruyi list --all":
                "信息：如果您意图唤起“列出所有软件包”这一旧版行为，请尝试 ruyi list --all",
            "List of available packages:": "可用软件包列表：",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(ruyi_exe, ["list"], env=isolated_env)
    try:
        child.expect_exact(_("fatal error: no filter specified for list operation"))
        child.expect_exact(_("info: for the old behavior of listing all packages, try ruyi list --all"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    child = spawn_ruyi(ruyi_exe, ["list", "--all"], env=isolated_env)
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("source/coremark")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["--porcelain", "list", "--name-contains", "coremark"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        records = [json.loads(line) for line in child.before.splitlines() if line]
    finally:
        child.close()
    assert child.exitstatus == 0
    assert len(records) == 1
    assert records[0]["ty"] == "pkglistoutput-v1"
    assert records[0]["category"] == "source"
    assert records[0]["name"] == "coremark"
    assert records[0]["vers"]

    child = spawn_ruyi(ruyi_exe, ["--porcelain", "list"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert child.before == ""
    finally:
        child.close()
    assert child.exitstatus == 1
