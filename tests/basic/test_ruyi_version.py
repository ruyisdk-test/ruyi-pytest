
import pexpect
import pytest
import shutil

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

    # TODO:
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["version"],
        env=isolated_env,
        timeout=5,
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
