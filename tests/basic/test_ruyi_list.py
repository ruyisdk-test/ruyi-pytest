
import pexpect
import re

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def test_ruyi_list(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Running on ": "上运行。",
            "Copyright (C) Institute of Software, Chinese Academy of Sciences (ISCAS).":
                "版权所有 (C) 中国科学院软件研究所 (ISCAS)。",
            "All rights reserved.": "所有权利保留。",
            "License: Apache-2.0": "许可证：Apache-2.0",
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
        child.expect_exact(_("* toolchain"))
        between = child.before
        assert _("Package declares") not in between
        child.expect(pexpect.EOF)
        after = child.before
        assert _("Package declares") not in after
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
        child.expect_exact(_("* Package kind:"))
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

    # ruyi list --name-contains 'gnu-milkv-milkv-duo-bin' --is-installed y
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-milkv-milkv-duo-bin", "--is-installed", "y"],
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

    # ruyi list --name-contains 'gnu-milkv-milkv-duo-bin' --is-installed n
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-milkv-milkv-duo-bin", "--is-installed", "n"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("toolchain/gnu-milkv-milkv-duo-bin")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi install gnu-milkv-milkv-duo-bin
    ruyi_install(ruyi_exe, ["gnu-milkv-milkv-duo-bin"], env=isolated_env)

    # ruyi list --name-contains 'gnu-milkv-milkv-duo-bin' --is-installed y
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-milkv-milkv-duo-bin", "--is-installed", "y"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact(_("installed"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains 'gnu-milkv-milkv-duo-bin' --is-installed n
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-milkv-milkv-duo-bin", "--is-installed", "n"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect(pexpect.EOF)
        after = child.before
        assert "toolchain/gnu-milkv-milkv-duo-bin" not in after
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
        timeout=5,
    )
    try:
        child.expect_exact(_("needs quirks:"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
