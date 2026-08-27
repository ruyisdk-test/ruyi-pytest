import hashlib
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import urllib.error
import urllib.request

from pathlib import Path
from typing import Callable, Dict, Iterator

import pytest


@pytest.fixture
def ruyi_exe() -> str:
    """Return the single PATH-resolved Ruyi executable used by the suite."""
    ruyi = shutil.which("ruyi")
    if ruyi is None:
        pytest.fail("`ruyi` not found in PATH")

    return ruyi


@pytest.fixture
def ruyi_version(ruyi_exe: str, isolated_env: Dict[str, str]) -> str:
    try:
        result = subprocess.run(
            [ruyi_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            env=isolated_env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        pytest.fail(f"failed to run `{ruyi_exe} --version`: {exc}")
    match = re.search(r"^Ruyi (\S+)", result.stdout, re.MULTILINE)
    if result.returncode != 0 or match is None:
        pytest.fail(f"failed to determine `{ruyi_exe}` version")
    return match.group(1)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ruyi-pytest/standalone-test"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        with destination.open("wb") as fp:
            shutil.copyfileobj(response, fp)


@pytest.fixture
def standalone_artifact(
    ruyi_version: str,
    isolated_env: Dict[str, str],
    tmp_path: Path,
) -> Path:
    """Download the official same-version standalone artifact automatically."""
    version_root = tmp_path / "standalone-download"
    version_root.mkdir(parents=True, exist_ok=True)
    machine = platform.machine().lower()
    if sys.platform == "linux":
        try:
            suffix = {
                "x86_64": "amd64",
                "amd64": "amd64",
                "aarch64": "arm64",
                "arm64": "arm64",
                "riscv64": "riscv64",
            }[machine]
        except KeyError:
            pytest.skip(f"no official Ruyi standalone artifact for host {machine!r}")
        asset = f"ruyi-{ruyi_version}.{suffix}"
    elif sys.platform == "darwin" and machine == "arm64":
        asset = f"ruyi-{ruyi_version}.macos-arm64"
    else:
        pytest.skip(
            "automatic standalone self-uninstall artifacts are unavailable "
            f"for {sys.platform}/{machine}"
        )
    channel = "testing" if "-" in ruyi_version else "releases"
    urls = [
        f"https://mirror.iscas.ac.cn/ruyisdk/ruyi/{channel}/{ruyi_version}/{asset}",
        f"https://github.com/ruyisdk/ruyi/releases/download/{ruyi_version}/{asset}",
    ]

    artifact = version_root / asset
    errors: list[str] = []
    for url in urls:
        try:
            _download(url, artifact)
            break
        except (OSError, TimeoutError, urllib.error.URLError) as exc:
            errors.append(f"{url}: {exc}")
    else:
        pytest.fail(
            "could not download the official standalone Ruyi artifact; "
            + " | ".join(errors)
        )

    if not artifact.is_file() or artifact.stat().st_size == 0:
        pytest.fail(f"downloaded standalone artifact is empty: {artifact}")
    validation_copy = version_root / "ruyi"
    shutil.copy2(artifact, validation_copy)
    validation_copy.chmod(
        validation_copy.stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )
    try:
        result = subprocess.run(
            [str(validation_copy), "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            env=isolated_env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        validation_copy.unlink(missing_ok=True)
        pytest.fail(f"failed to run downloaded standalone Ruyi: {exc}")
    match = re.search(r"^Ruyi (\S+)", result.stdout, re.MULTILINE)
    actual_version = match.group(1) if match is not None else None
    if result.returncode != 0 or actual_version != ruyi_version:
        validation_copy.unlink(missing_ok=True)
        pytest.fail(
            "downloaded standalone Ruyi version does not match ruyi_exe: "
            f"{actual_version!r} != {ruyi_version!r}"
        )

    validation_copy.unlink()
    return artifact


@pytest.fixture
def standalone_exe(
    standalone_artifact: Path,
    tmp_path: Path,
) -> Iterator[Callable[[str], Path]]:
    """Return temporary copies of the automatically downloaded artifact."""
    source_digest = _sha256(standalone_artifact)

    def copy_for_test(label: str) -> Path:
        copy_root = tmp_path / "standalone" / label
        copy_root.mkdir(parents=True, exist_ok=True)
        destination = copy_root / "ruyi"
        shutil.copy2(standalone_artifact, destination)
        destination.chmod(
            destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        return destination

    yield copy_for_test

    if not standalone_artifact.is_file() or _sha256(standalone_artifact) != source_digest:
        pytest.fail("the downloaded standalone Ruyi artifact was modified")


@pytest.fixture
def ruyi_dep() -> bool:
    deps = [
        "bash",
        "bzip2",
        "gunzip",
        "lz4",
        "tar",
        "xz",
        "zstd",
        "unzip"
    ]

    for d in deps:
        if not shutil.which(d):
            pytest.fail(f"`{d}` not found in PATH")

    return True


@pytest.fixture
def ruyi_dep_provisioning(ruyi_dep: bool) -> bool:
    deps = [
        "sudo",
        "dd",
        "fastboot"
    ]

    if not ruyi_dep:
        return False

    for d in deps:
        if not shutil.which(d):
            pytest.fail(f"`{d}` not found in PATH")

    return True


@pytest.fixture
def ruyi_build_dep(ruyi_dep: bool) -> bool:
    deps = [
        "make",
    ]

    if not ruyi_dep:
        return False

    for d in deps:
        if not shutil.which(d):
            pytest.fail(f"`{d}` not found in PATH")

    return True


@pytest.fixture
def isolated_env(tmp_path: Path) -> Dict[str, str]:
    root = tmp_path

    home = root / "ruyisdk"
    config = home / "config"
    cache = home / "cache"
    data = home / "data"
    state = home / "state"
    etc = root / "etc"
    usr_share = root / "usr-share"

    for path in (home, config, cache, data, state, etc, usr_share):
        path.mkdir()

    env = os.environ.copy()
    for key in (
        "LANGUAGE",
        "LC_ALL",
        "LC_MESSAGES",
        "RUYI_DEBUG",
        "RUYI_DEBUG_FORCE_FIRST_RUN",
        "RUYI_EXPERIMENTAL",
        "RUYI_FORCE_ALLOW_ROOT",
        "RUYI_OVERRIDE_FETCHER",
        "RUYI_TELEMETRY_OPTOUT",
        "RUYI_VENV",
        "NUITKA_ONEFILE_BINARY",
        "NUITKA_ONEFILE_PARENT",
        "_ARGCOMPLETE",
    ):
        env.pop(key, None)
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(config)
    env["XDG_CACHE_HOME"] = str(cache)
    env["XDG_DATA_HOME"] = str(data)
    env["XDG_STATE_HOME"] = str(state)
    env["XDG_CONFIG_DIRS"] = str(etc)
    env["XDG_DATA_DIRS"] = str(usr_share)

    # disable rich text
    env["TERM"] = "dumb"

    return env


@pytest.fixture
def standalone_env(isolated_env: Dict[str, str]) -> Dict[str, str]:
    """Use a temporary global policy that permits the copied binary to uninstall."""
    etc = Path(isolated_env["XDG_CONFIG_DIRS"].split(os.pathsep)[0])
    global_config_dir = etc / "ruyi"
    global_config_dir.mkdir(parents=True, exist_ok=True)
    (global_config_dir / "config.toml").write_text(
        "[installation]\n"
        "externally_managed = false\n"
        "disable_oobe = true\n"
        "disable_telemetry_by_default = true\n",
        encoding="utf-8",
    )
    return isolated_env
