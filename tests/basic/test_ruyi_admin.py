import hashlib
import json
import pexpect
import tomllib
import zipfile

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


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
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: invalid --var spec 'invalid': expected KEY=VALUE":
                "致命错误：无效的 --var 规范 'invalid'：预期格式为 KEY=VALUE",
            "fatal error: invalid --var spec '=value': empty key":
                "致命错误：无效的 --var 规范 '=value'：键为空",
        },
    })
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

    for spec, message in (
        ("invalid", "fatal error: invalid --var spec 'invalid': expected KEY=VALUE"),
        ("=value", "fatal error: invalid --var spec '=value': empty key"),
    ):
        child = spawn_ruyi(
            ruyi_exe,
            ["admin", "build-package", "--var", spec, str(recipe)],
            env=isolated_env,
        )
        try:
            child.expect_exact(_(message))
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


def test_ruyi_admin_checksum_options(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: invalid restrict kinds given: ['invalid']":
                "致命错误：给出了无效的 restrict 类型：['invalid']",
        },
    })
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    payload_dir = tmp_path / "payload files"
    payload_dir.mkdir()
    first = payload_dir / "first.bin"
    second = payload_dir / "second.bin"
    first.write_bytes(b"first payload\n")
    second.write_bytes(b"second payload\n")

    child = spawn_ruyi(
        ruyi_exe,
        [
            "admin", "checksum", "-f", "toml", "--restrict", "fetch,mirror",
            str(first), str(second),
        ],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        data = tomllib.loads(child.before)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert len(data["distfiles"]) == 2
    assert data["distfiles"][0]["name"] == first.name
    assert data["distfiles"][0]["size"] == first.stat().st_size
    assert data["distfiles"][0]["restrict"] == ["fetch", "mirror"]
    assert data["distfiles"][0]["checksums"]["sha256"] == hashlib.sha256(first.read_bytes()).hexdigest()
    assert data["distfiles"][0]["checksums"]["sha512"] == hashlib.sha512(first.read_bytes()).hexdigest()
    assert data["distfiles"][1]["name"] == second.name

    archive = tmp_path / "payload.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("a.txt", b"abc")
        zf.writestr("nested/b.txt", b"12345")

    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "checksum", "--install-size", str(archive)],
        env=isolated_env,
    )
    try:
        child.expect_exact("#   install_size = 8")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "checksum", "--restrict", "invalid", str(first)],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("fatal error: invalid restrict kinds given: ['invalid']"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1


def test_ruyi_admin_check_repo_and_porcelain(ruyi_exe: str, isolated_env: Dict[str, str], tmp_path: Path):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "config.toml").write_text(
        'ruyi-repo = "v1"\n\n'
        '[[mirrors]]\n'
        'id = "test"\n'
        'urls = ["https://example.invalid/dist/"]\n',
        encoding="utf-8",
    )

    malformed = repo_root / "packages" / "source" / "ignored" / "1.0.0.toml"
    malformed.parent.mkdir(parents=True)
    malformed.write_text('format = "v1"\n[', encoding="utf-8")

    selected = repo_root / "packages" / "board-image" / "selected" / "1.0.0.toml"
    selected.parent.mkdir(parents=True)
    selected.write_text(
        'format = "v1"\n\n'
        '[[distfiles]]\n'
        'size = 0\n'
        'name = "src.tar.zst"\n\n'
        '[distfiles.checksums]\n'
        f'sha256 = "{"0" * 64}"\n\n'
        '[metadata]\n'
        'vendor = { eula = "", name = "Test Vendor" }\n'
        'desc = "Test package"\n\n'
        '[source]\n'
        'distfiles = ["src.tar.zst"]\n',
        encoding="utf-8",
    )

    child = spawn_ruyi(
        ruyi_exe,
        [
            "admin", "check", "--repo", str(repo_root),
            "--only-packages", "--category-is", "board-image",
        ],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()
    assert child.exitstatus == 1
    assert "RYC0001" in output
    assert str(selected) in output
    assert str(malformed) not in output
    assert "RYC0002" not in output

    child = spawn_ruyi(
        ruyi_exe,
        ["--porcelain", "admin", "check", "--file", str(selected)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        records = [json.loads(line) for line in child.before.splitlines() if line]
    finally:
        child.close()
    assert child.exitstatus == 1
    assert len(records) == 1
    assert records[0]["ty"] == "checkdiagnostic-v1"
    assert records[0]["code"] == "RYC0001"
    assert records[0]["check"] == "format"
    assert records[0]["path"] == str(selected)

    child = spawn_ruyi(
        ruyi_exe,
        ["admin", "check", "--file", str(selected), "--repo", str(repo_root)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 2
