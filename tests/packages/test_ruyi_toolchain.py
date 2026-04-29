
import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def test_ruyi_venv_xthead(ruyi_exe: str, ruyi_build_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    ruyi_install(ruyi_exe, ["gnu-plct-xthead"], env=isolated_env)

    venv_path = tmp_path / "rit-ruyi-basic-ruyi-xthead"
    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "gnu-plct-xthead", "sipeed-lpi4a", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    source_path = tmp_path / "coremark"
    source_path.mkdir()
    child = spawn_ruyi(
        ruyi_exe,
        ["extract", "--extract-without-subdir", "coremark(1.0.1)", ],
        env=isolated_env,
        timeout=10 * 60,
        cwd=str(source_path),
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'''
source "{venv_path}/bin/ruyi-activate"
sed -i 's/\\bgcc\\b/riscv64-plctxthead-linux-gnu-gcc/g' linux64/core_portme.mak
make PORT_DIR=linux64 link
riscv64-plctxthead-linux-gnu-readelf -h ./coremark.exe
ruyi-deactivate
''',
        ],
        env=isolated_env,
        timeout=60,
        cwd=str(source_path),
    )
    try:
        child.expect_exact("riscv64-plctxthead-linux-gnu-gcc")
        child.expect_exact("Link performed along with compile")
        child.expect_exact("ELF Header:")
        child.expect_exact("ELF64")
        child.expect_exact("RISC-V")
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()
