
import os
import pexpect
import platform
import pytest

from pathlib import Path
from typing import Dict

from tests.helpers import ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def write_hello_elf(hello_elf: Path):
    hello_elf.write_bytes(
        bytes.fromhex(
            "7f454c46020101000000000000000000"
            "02003e0001000000"
            "7800400000000000"
            "4000000000000000"
            "0000000000000000"
            "00000000"
            "4000"
            "3800"
            "0100"
            "0000"
            "0000"
            "0000"
            "01000000"
            "05000000"
            "0000000000000000"
            "0000400000000000"
            "0000400000000000"
            "a500000000000000"
            "a500000000000000"
            "0010000000000000"
            "b801000000"
            "bf01000000"
            "488d3510000000"
            "ba0c000000"
            "0f05"
            "b83c000000"
            "31ff"
            "0f05"
            "68656c6c6f20776f726c640a"
        )
    )
    os.chmod(hello_elf, 0o755)


@pytest.mark.skipif(platform.machine() != "riscv64", reason="riscv64 only")
def test_box64(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    ruyi_install(ruyi_exe, ["box64-upstream"], env=isolated_env)

    box64_bins = list(
        (Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "binaries" / "riscv64").glob("box64-upstream-*/bin/box64")
    )
    assert box64_bins, "box64 binary not found"
    assert len(box64_bins) == 1

    child = spawn_ruyi(
        str(box64_bins[0]),
        ["--version"],
        env=isolated_env,
    )
    try:
        child.expect_exact("Box64")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # test hello_elf run
    hello_elf = tmp_path / "hello-x86_64"
    write_hello_elf(hello_elf)

    child = spawn_ruyi(
        str(box64_bins[0]),
        args=[str(hello_elf)],
        env=isolated_env,
    )
    try:
        child.expect_exact("hello world")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0


@pytest.mark.skipif(platform.machine() != "x86_64", reason="x86_64 only")
def test_hello_elf_x86_64(isolated_env: Dict[str, str], tmp_path: Path):
    """
    check hello_elf runnable
    :param isolated_env:
    :param tmp_path:
    :return:
    """

    hello_elf = tmp_path / "hello-x86_64"
    write_hello_elf(hello_elf)

    hello_elf = tmp_path / "hello-x86_64"
    write_hello_elf(hello_elf)
    child = spawn_ruyi(
        str(hello_elf),
        args=[],
        env=isolated_env,
    )
    try:
        child.expect_exact("hello world")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
