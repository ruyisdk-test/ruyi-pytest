import platform
import pexpect
import pytest
import tomllib

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


WLINK_HOSTS = {"aarch64", "riscv64", "x86_64"}


def test_ruyi_venv(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):
    """
    test venv
    :param ruyi_exe:
    :param ruyi_dep:
    :param isolated_env:
    :param tmp_path:
    :return:
    """
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            r"info: Creating a Ruyi virtual environment at .*": r"信息：正在在 .* 创建 Ruyi 虚拟环境...",
            "info: The virtual environment is now created.": "信息：现已创建完成虚拟环境。",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    ruyi_install(
        ruyi_exe,
        pkgs=["llvm-upstream", "gnu-plct"],
        env=isolated_env,
    )

    # venv
    venv_path = tmp_path / "rit-ruyi-basic-ruyi-venv"

    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "--toolchain", "gnu-plct", "generic", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(_(r"info: Creating a Ruyi virtual environment at .*"))
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect_exact("ruyi-deactivate")
        child.expect_exact(str((venv_path / "sysroot").absolute()))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # venv cmdline
    shell_env = isolated_env.copy()
    shell_env["PS1"] = "$ "
    child = spawn_ruyi(
        "bash",
        ["--noprofile", "--norc", "-i"],
        env=shell_env,
    )
    try:
        child.expect_exact("$ ")
        child.sendline('oldps1="$PS1"')

        child.sendline(f'source "{venv_path}/bin/ruyi-activate"')
        child.expect_exact(f"«Ruyi {venv_path.name}» $ ")

        child.sendline("riscv64-plct-linux-gnu-gcc --version")
        child.expect_exact("riscv64-plct-linux-gnu-gcc")
        child.expect_exact("Copyright")

        child.sendline("ruyi-deactivate")
        child.expect_exact("$ ")

        child.sendline('[[ "$PS1" == "$oldps1" ]]; echo $?')
        child.expect_exact("0")

        child.sendline("exit")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # --sysroot-from
    venv_path = tmp_path / "rit-ruyi-basic-ruyi-llvm"
    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "llvm-upstream", "--sysroot-from", "gnu-plct", "generic", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(_(r"info: Creating a Ruyi virtual environment at .*"))
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect_exact("ruyi-deactivate")
        child.expect_exact(str((venv_path / "sysroot").absolute()))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert (venv_path / "sysroot").exists()
    assert (venv_path / "bin" / "clang").exists()

    hello_c = tmp_path / "hello_ruyi.c"
    hello_c.write_text(
        '#include <stdio.h>\n\n'
        'int main()\n'
        '{\n'
        '    printf("hello, ruyi\\n");\n\n'
        '    return 0;\n'
        '}\n',
        encoding="utf-8",
    )

    # clang build
    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'source "{venv_path}/bin/ruyi-activate" && '
            f'clang -O3 "{hello_c}" -o "{tmp_path / "hello_ruyi.o"}" && '
            'echo "ret $?" && '
            'ruyi-deactivate',
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact("ret 0")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # run on riscv
    if platform.machine() != "riscv64":
        return

    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'source "{venv_path}/bin/ruyi-activate" && ' +
            f'"{tmp_path / "hello_ruyi.o"}" && '
            'echo "ret $?" && '
            'ruyi-deactivate',
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact("hello, ruyi")
        child.expect_exact("ret 0")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0


def test_ruyi_venv_sysroot_options(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            r"info: Creating a Ruyi virtual environment .*": r"信息：正在在 .* 创建 Ruyi 虚拟环境...",
            "info: The virtual environment is now created.": "信息：现已创建完成虚拟环境。",
            "fatal error: at most one of --copy-sysroot-from-pkg, --copy-sysroot-from-dir, --symlink-sysroot-from-dir, and --project-sysroot-from-rootfs may be specified":
                "致命错误：至多只能指定 --copy-sysroot-from-pkg、--copy-sysroot-from-dir、--symlink-sysroot-from-dir 和 --project-sysroot-from-rootfs 中的一个",
            "fatal error: --without-sysroot cannot be combined with a sysroot source option":
                "致命错误：--without-sysroot 不能与任何 sysroot 来源选项同时使用",
            "fatal error: You have to specify at least one toolchain atom for now, e.g. `-t gnu-plct`":
                "致命错误：当前，您必须至少指定一个工具链 atom，例如 `-t gnu-plct`",
            "fatal error: profile 'no-such-profile' not found":
                "致命错误：未找到配置文件 'no-such-profile'",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        [
            "venv", "-t", "gnu-plct",
            "--copy-sysroot-from-dir", str(tmp_path / "one"),
            "--symlink-sysroot-from-dir", str(tmp_path / "two"),
            "generic", str(tmp_path / "invalid-multiple-sysroots"),
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: at most one of --copy-sysroot-from-pkg, --copy-sysroot-from-dir, --symlink-sysroot-from-dir, and --project-sysroot-from-rootfs may be specified"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "generic", str(tmp_path / "missing-toolchain")],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: You have to specify at least one toolchain atom for now, e.g. `-t gnu-plct`"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "gnu-plct", "no-such-profile", str(tmp_path / "unknown-profile")],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: profile 'no-such-profile' not found"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    child = spawn_ruyi(
        ruyi_exe,
        [
            "venv", "-t", "gnu-plct", "--without-sysroot",
            "--copy-sysroot-from-dir", str(tmp_path / "one"),
            "generic", str(tmp_path / "invalid-without-sysroot"),
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: --without-sysroot cannot be combined with a sysroot source option"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    packages = ["gnu-plct"]
    if platform.machine() in WLINK_HOSTS:
        packages.append("board-util/wlink")
    ruyi_install(ruyi_exe, pkgs=packages, env=isolated_env)

    sysroot = tmp_path / "sysroot"
    (sysroot / "usr" / "include").mkdir(parents=True)
    (sysroot / "usr" / "include" / "test.h").write_text("test\n", encoding="utf-8")
    rootfs = tmp_path / "rootfs"
    (rootfs / "usr" / "include").mkdir(parents=True)
    (rootfs / "usr" / "include" / "rootfs.h").write_text("rootfs\n", encoding="utf-8")

    without_sysroot = tmp_path / "without-sysroot"
    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "gnu-plct", "--without-sysroot", "--name", "CustomName", "generic", str(without_sysroot)],
        env=isolated_env,
    )
    try:
        child.expect(_(r"info: Creating a Ruyi virtual environment .*"))
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert not (without_sysroot / "sysroot").exists()

    shell_env = isolated_env.copy()
    shell_env["PS1"] = "$ "
    child = spawn_ruyi("bash", ["--noprofile", "--norc", "-i"], env=shell_env)
    try:
        child.expect_exact("$ ")
        child.sendline(f'source "{without_sysroot}/bin/ruyi-activate"')
        child.expect_exact("«Ruyi CustomName» $ ")
        child.sendline("ruyi-deactivate")
        child.expect_exact("$ ")
        child.sendline("exit")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    copied = tmp_path / "copied-sysroot"
    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "gnu-plct", "--copy-sysroot-from-dir", str(sysroot), "generic", str(copied)],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert (copied / "sysroot" / "usr" / "include" / "test.h").exists()

    symlinked = tmp_path / "symlinked-sysroot"
    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "gnu-plct", "--symlink-sysroot-from-dir", str(sysroot), "generic", str(symlinked)],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert (symlinked / "sysroot").is_symlink()
    assert (symlinked / "sysroot").resolve() == sysroot.resolve()

    projected = tmp_path / "projected-sysroot"
    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "gnu-plct", "--project-sysroot-from-rootfs", str(rootfs), "generic", str(projected)],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert (projected / "sysroot" / "usr" / "include" / "rootfs.h").exists()

    if platform.machine() in WLINK_HOSTS:
        extra = tmp_path / "extra-commands"
        child = spawn_ruyi(
            ruyi_exe,
            ["venv", "-t", "gnu-plct", "--extra-commands-from", "board-util/wlink", "generic", str(extra)],
            env=isolated_env,
        )
        try:
            child.expect_exact(_("info: The virtual environment is now created."))
            child.expect(pexpect.EOF)
        finally:
            child.close()
        assert child.exitstatus == 0
        assert (extra / "bin" / "wlink").exists()

        with (extra / "ruyi-venv.toml").open("rb") as fp:
            metadata = tomllib.load(fp)["metadata"]
        assert metadata["packages"]["extra"][0]["category"] == "board-util"
        assert metadata["packages"]["extra"][0]["name"] == "wlink"

        child = spawn_ruyi(str(extra / "bin" / "wlink"), ["--help"], env=isolated_env)
        try:
            child.expect_exact("Usage:")
            child.expect_exact("wlink")
            child.expect(pexpect.EOF)
        finally:
            child.close()
        assert child.exitstatus == 0


@pytest.mark.skipif(platform.machine() != "x86_64", reason="x86_64 only")
def test_ruyi_venv_emulator(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):
    """
    test venv
    :param ruyi_exe:
    :param ruyi_dep:
    :param isolated_env:
    :param tmp_path:
    :return:
    """
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            r"info: Creating a Ruyi virtual environment at .*": r"信息：正在在 .* 创建 Ruyi 虚拟环境...",
            "info: The virtual environment is now created.": "信息：现已创建完成虚拟环境。",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    ruyi_install(
        ruyi_exe,
        pkgs=["llvm-upstream", "gnu-plct", "qemu-user-riscv-upstream"],
        env=isolated_env,
    )

    # venv
    venv_path = tmp_path / "rit-ruyi-basic-ruyi-venv"

    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "--toolchain", "gnu-plct", "-e", "qemu-user-riscv-upstream", "generic", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(_(r"info: Creating a Ruyi virtual environment at .*"))
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect_exact("ruyi-deactivate")
        child.expect_exact(str((venv_path / "sysroot").absolute()))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # venv cmdline
    shell_env = isolated_env.copy()
    shell_env["PS1"] = "$ "
    child = spawn_ruyi(
        "bash",
        ["--noprofile", "--norc", "-i"],
        env=shell_env,
    )
    try:
        child.expect_exact("$ ")
        child.sendline('oldps1="$PS1"')

        child.sendline(f'source "{venv_path}/bin/ruyi-activate"')
        child.expect_exact(f"«Ruyi {venv_path.name}» $ ")

        child.sendline("riscv64-plct-linux-gnu-gcc --version")
        child.expect_exact("riscv64-plct-linux-gnu-gcc")
        child.expect_exact("Copyright")

        child.sendline("ruyi-deactivate")
        child.expect_exact("$ ")

        child.sendline('[[ "$PS1" == "$oldps1" ]]; echo $?')
        child.expect_exact("0")

        child.sendline("exit")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    venv_path = tmp_path / "rit-ruyi-basic-ruyi-llvm"
    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "llvm-upstream", "--copy-sysroot-from-pkg", "gnu-plct", "-e", "qemu-user-riscv-upstream", "generic", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(_(r"info: Creating a Ruyi virtual environment at .*"))
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect_exact("ruyi-deactivate")
        child.expect_exact(str((venv_path / "sysroot").absolute()))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert (venv_path / "sysroot").exists()
    assert (venv_path / "bin" / "clang").exists()
    assert (venv_path / "bin" / "ruyi-qemu").exists()

    hello_c = tmp_path / "hello_ruyi.c"
    hello_c.write_text(
        '#include <stdio.h>\n\n'
        'int main()\n'
        '{\n'
        '    printf("hello, ruyi\\n");\n\n'
        '    return 0;\n'
        '}\n',
        encoding="utf-8",
    )

    # clang build
    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'source "{venv_path}/bin/ruyi-activate" && '
            f'clang -O3 "{hello_c}" -o "{tmp_path / "hello_ruyi.o"}" && '
            'echo "ret $?" && '
            'ruyi-deactivate',
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact("ret 0")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # run
    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'source "{venv_path}/bin/ruyi-activate" && ' +
            f'ruyi-qemu "{tmp_path / "hello_ruyi.o"}" && '
            'echo "ret $?" && '
            'ruyi-deactivate',
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact("hello, ruyi")
        child.expect_exact("ret 0")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
