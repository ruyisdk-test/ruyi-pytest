
import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_version(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Running on ": "上运行。",
            "Copyright (C) Institute of Software, Chinese Academy of Sciences (ISCAS).":
                "版权所有 (C) 中国科学院软件研究所 (ISCAS)。",
            "All rights reserved.": "所有权利保留。",
            "License: Apache-2.0": "许可证：Apache-2.0",
        },
    })

    # See: https://github.com/ruyisdk/ruyi/issues/454

    child = spawn_ruyi(
        ruyi_exe,
        ["version"],
        env=isolated_env,
    )
    try:
        child.expect(r"Ruyi (\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?)")
        child.expect_exact(_("Running on "))
        child.expect_exact(_("Copyright (C) Institute of Software, Chinese Academy of Sciences (ISCAS)."))
        child.expect_exact(_("All rights reserved."))
        child.expect_exact(_("License: Apache-2.0"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
    assert not (Path(isolated_env["XDG_STATE_HOME"]) / "ruyi" / "telemetry").exists()

def test_ruyi_top_level_options(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "usage: ruyi": "用法：ruyi",
        },
    })

    for args in (["-V"], ["--version"], ["--porcelain", "version"]):
        child = spawn_ruyi(
            ruyi_exe,
            list(args),
            env=isolated_env,
        )
        try:
            child.expect_exact("Ruyi ")
            child.expect(pexpect.EOF)
        finally:
            child.close()
        assert child.exitstatus == 0

    assert not (Path(isolated_env["XDG_STATE_HOME"]) / "ruyi" / "telemetry").exists()

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(ruyi_exe, [], env=isolated_env)
    try:
        child.expect_exact(_("usage: ruyi"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["no-such-subcommand"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 2
