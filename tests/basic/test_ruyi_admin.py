import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_admin(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    this_file = Path(__file__).resolve()
    test_toml = tmp_path / "test.toml"

    # ruyi admin checksum $0
    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "checksum", str(this_file)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()
    assert child.exitstatus == 0

    lines = output.splitlines()
    assert lines[0] == "[[distfiles]]"
    assert lines[1].startswith("name = ")
    assert lines[2].startswith("size = ")
    assert lines[3] == ""
    assert lines[4] == "[distfiles.checksums]"
    assert lines[5].startswith("sha256 = ")
    assert lines[6].startswith("sha512 = ")

    # ruyi admin checksum --format toml $0
    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "checksum", "--format", "toml", str(this_file)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()
    assert child.exitstatus == 0

    lines = output.splitlines()
    assert lines[0] == "[[distfiles]]"
    assert lines[1].startswith("name = ")
    assert lines[2].startswith("size = ")
    assert lines[3] == ""
    assert lines[4] == "[distfiles.checksums]"
    assert lines[5].startswith("sha256 = ")
    assert lines[6].startswith("sha512 = ")

    test_toml.write_text(
        'format = "v1"\n'
        '[metadata]\n'
        'vendor={name ="kosaka",eula=""}\n'
        'desc= "test metadata"\n'
        + output,
        encoding="utf-8",
    )

    # ruyi admin check -f "$tmp_path"/test.toml --check parse --check format
    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "check", "-f", str(test_toml), "--check", "parse", "--check", "format"],
        env=isolated_env,
    )
    try:
        child.expect_exact("error RYC0001: manifest is not canonical")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    # ruyi admin check -f "$tmp_path"/test.toml --check parse
    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "check", "-f", str(test_toml), "--check", "parse"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi admin format-manifest "$tmp_path"/test.toml
    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "format-manifest", str(test_toml)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    formatted = test_toml.read_text(encoding="utf-8")
    lines = formatted.splitlines()

    assert lines[0] == 'format = "v1"'
    assert lines[1] == ""
    assert lines[2] == "[metadata]"
    assert lines[3] == 'desc = "test metadata"'
    assert lines[4] == 'vendor = { name = "kosaka", eula = "" }'
    assert lines[5] == ""
    assert lines[6] == "[[distfiles]]"
    assert lines[7].startswith("name = ")
    assert lines[8].startswith("size = ")
    assert lines[9] == ""
    assert lines[10] == "[distfiles.checksums]"
    assert lines[11].startswith("sha256 = ")
    assert lines[12].startswith("sha512 = ")

    # ruyi admin check -f "$tmp_path"/test.toml
    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "check", "-f", str(test_toml)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0


def test_ruyi_admin_default_strip_components(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    """
    Ruyi will remove `strip_components = 1` as it is default behavior
    :param ruyi_exe:
    :param isolated_env:
    :param tmp_path:
    :return:
    """
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    this_file = Path(__file__).resolve()
    test_toml = tmp_path / "test.toml"

    test_toml.write_text(
        'format = "v1"\n'
        '[metadata]\n'
        'desc = "Buildroot SDK & FreeRTOS image for Sipeed LicheeRV Nano, 20260114"\n'
        'vendor = { name = "Sipeed", eula = "" }\n'
        'upstream_version = "20260114"\n'
        '[[distfiles]]\n'
        'name = "2026-01-14-16-03-d4003f.tar.xz"\n'
        'size = 171913924\n'
        'urls = [\n'
        '  "https://github.com/sipeed/LicheeRV-Nano-Build/releases/download/20260114/2026-01-14-16-03-d4003f.tar.xz",\n'
        ']\n'
        'restrict = ["mirror"]\n'
        'strip_components = 1\n'
        '[distfiles.checksums]\n'
        'sha256 = "d6478170e923615ca28c97592a2c68a67971e6d07fcb967371b58791938698dd"\n'
        'sha512 = "63b2ba457c227f1f171af669d80663d2b92a7de1b23cc7975cba0a2b3924d50608b71cf6978735a981b666da709d5b30103124ab9a37fe49e6080ca826c5e475"\n'
        '[blob]\n'
        'distfiles = [\n'
        '  "2026-01-14-16-03-d4003f.tar.xz",\n'
        ']\n'
        '[provisionable]\n'
        'strategy = "dd-v1"\n'
        '[provisionable.partition_map]\n'
        'disk = "2026-01-14-16-03-d4003f.img"\n',
        encoding="utf-8",
    )

    # ruyi admin format-manifest "$tmp_path"/test.toml
    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "format-manifest", str(test_toml)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    formatted = test_toml.read_text(encoding="utf-8")
    lines = formatted.splitlines()

    assert "" in lines
    assert "strip_components = 1" not in lines


def test_ruyi_admin_build_package(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    recipe = tmp_path / "recipe.star"
    recipe.write_text("not valid starlark\n", encoding="utf-8")

    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "build-package", "--dry-run", str(recipe)],
        env=isolated_env,
    )
    try:
        child.expect_exact("ruyi-build-recipes.toml")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1


def test_ruyi_admin_run_plugin_cmd(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "run-plugin-cmd", "no-such-cmd"],
        env=isolated_env,
    )
    try:
        child.expect_exact("FileNotFoundError")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1


def test_ruyi_admin_issue430(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    """
    ruyi 0.46.0: ruyi admin format-manifest automatically remove distfiles[].strip_components < 2
    See: https://github.com/ruyisdk/ruyi/issues/430
    :param ruyi_exe:
    :param isolated_env:
    :param tmp_path:
    :return:
    """
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    this_file = Path(__file__).resolve()
    test_toml = tmp_path / "test.toml"

    test_toml.write_text(
        'format = "v1"\n'
        '[metadata]\n'
        'desc = "Buildroot SDK & FreeRTOS image for Sipeed LicheeRV Nano, 20260114"\n'
        'vendor = { name = "Sipeed", eula = "" }\n'
        'upstream_version = "20260114"\n'
        '[[distfiles]]\n'
        'name = "2026-01-14-16-03-d4003f.tar.xz"\n'
        'size = 171913924\n'
        'urls = [\n'
        '  "https://github.com/sipeed/LicheeRV-Nano-Build/releases/download/20260114/2026-01-14-16-03-d4003f.tar.xz",\n'
        ']\n'
        'restrict = ["mirror"]\n'
        'strip_components = 0\n'
        '[distfiles.checksums]\n'
        'sha256 = "d6478170e923615ca28c97592a2c68a67971e6d07fcb967371b58791938698dd"\n'
        'sha512 = "63b2ba457c227f1f171af669d80663d2b92a7de1b23cc7975cba0a2b3924d50608b71cf6978735a981b666da709d5b30103124ab9a37fe49e6080ca826c5e475"\n'
        '[blob]\n'
        'distfiles = [\n'
        '  "2026-01-14-16-03-d4003f.tar.xz",\n'
        ']\n'
        '[provisionable]\n'
        'strategy = "dd-v1"\n'
        '[provisionable.partition_map]\n'
        'disk = "2026-01-14-16-03-d4003f.img"\n',
        encoding="utf-8",
    )

    # ruyi admin format-manifest "$tmp_path"/test.toml
    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "format-manifest", str(test_toml)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    formatted = test_toml.read_text(encoding="utf-8")
    lines = formatted.splitlines()

    assert "" in lines
    assert "strip_components = 0" in lines