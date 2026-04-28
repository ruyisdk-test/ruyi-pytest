
import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_install_and_extract(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path,):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            r"info: extracting ruyisdk-demo-\S+ for package ruyisdk-demo-\S+":
                r"信息：正在为软件包 ruyisdk-demo-\S+ 解压缩 ruyisdk-demo-\S+",
            r"info: package ruyisdk-demo-\S+ has been extracted to None":
                r"信息：软件包 ruyisdk-demo-\S+ 已被解压缩到 None",
            r"info: package ruyisdk-demo-\S+ has been extracted to (ruyisdk-demo-\S+)":
                r"信息：软件包 ruyisdk-demo-\S+ 已被解压缩到 (ruyisdk-demo-\S+)",
            "info: extracting coremark-1.01.tar.gz for package coremark-1.0.1":
                "信息：正在为软件包 coremark-1.0.1 解压缩 coremark-1.01.tar.gz",
            "info: package coremark-1.0.1 has been extracted to coremark-1.0.1":
                "信息：软件包 coremark-1.0.1 已被解压缩到 coremark-1.0.1",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi extract --extract-without-subdir
    # with `strip_components = 2`
    # default behaviour before 0.42.0
    # see: https://github.com/ruyisdk/ruyi/issues/371
    test_path = tmp_path / "test_extract_without_subdir"
    test_path.mkdir()
    child = spawn_ruyi(
        ruyi_exe,
        ["extract", "--extract-without-subdir", "ruyisdk-demo"],
        env=isolated_env,
        timeout=10 * 60,
        cwd=str(test_path),
    )
    try:
        child.expect(_(r"info: extracting ruyisdk-demo-\S+ for package ruyisdk-demo-\S+"))
        # TODO: we should open a new issue
        child.expect(_(r"info: package ruyisdk-demo-\S+ has been extracted to None"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
    assert (test_path / "README.md").exists()
    assert (test_path / "rvv-autovec" / "Makefile").exists()
    assert (test_path / "rvv-autovec" / "test.c").exists()

    # ruyi extract
    test_path = tmp_path / "test_extract"
    test_path.mkdir()
    child = spawn_ruyi(
        ruyi_exe,
        ["extract", "ruyisdk-demo"],
        env=isolated_env,
        timeout=10 * 60,
        cwd=str(test_path),
    )
    try:
        child.expect(_(r"info: extracting ruyisdk-demo-\S+ for package ruyisdk-demo-\S+"))
        child.expect(_(r"info: package ruyisdk-demo-\S+ has been extracted to (ruyisdk-demo-\S+)"))
        extracted = child.match.group(1)
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
    assert (test_path / extracted).exists()
    assert (test_path / extracted / "README.md").exists()
    assert (test_path / extracted / "rvv-autovec" / "Makefile").exists()
    assert (test_path / extracted / "rvv-autovec" / "test.c").exists()

    # ruyi extract 'coremark(1.0.1)'
    # with `strip_components = 2`
    test_path = tmp_path / "test_extract_coremark"
    test_path.mkdir()
    child = spawn_ruyi(
        ruyi_exe,
        ["extract", "coremark(1.0.1)"],
        env=isolated_env,
        timeout=10 * 60,
        cwd=str(test_path),
    )
    try:
        child.expect_exact(_("info: extracting coremark-1.01.tar.gz for package coremark-1.0.1"))
        child.expect_exact(_("info: package coremark-1.0.1 has been extracted to coremark-1.0.1"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
    assert (test_path / "coremark-1.0.1").exists()
    assert (test_path / "coremark-1.0.1" / "README.md").exists()
    assert (test_path / "coremark-1.0.1" / "Makefile").exists()
