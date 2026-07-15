
import os
import pytest
import re
import shutil
import subprocess

from functools import lru_cache
from packaging.version import InvalidVersion, Version
from pathlib import Path
from typing import Dict


MIN_RUYI_VERSION = Version("0.51.0b20260714")


@lru_cache(maxsize=None)
def _read_ruyi_version(ruyi: str) -> str:
    result = subprocess.run(
        [ruyi, "--version"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    match = re.search(r"^Ruyi (\S+)", result.stdout)
    if result.returncode != 0 or match is None:
        pytest.fail(f"failed to determine `{ruyi}` version")

    version_text = match.group(1)
    try:
        version = Version(version_text)
    except InvalidVersion:
        pytest.fail(f"`{ruyi}` reported an invalid version: {version_text!r}")
    if version < MIN_RUYI_VERSION:
        pytest.fail(
            f"`{ruyi}` is too old; Ruyi 0.51.0-beta.20260714 or newer is required"
        )

    return version_text


@pytest.fixture(scope="session")
def ruyi_exe() -> str:
    ruyi = shutil.which("ruyi")
    if ruyi is None:
        pytest.fail("`ruyi` not found in PATH")

    _read_ruyi_version(ruyi)

    return ruyi


@pytest.fixture(scope="session")
def ruyi_version(ruyi_exe: str) -> str:
    return _read_ruyi_version(ruyi_exe)


@pytest.fixture
def ruyi_dep() -> bool:
    deps = [
        "bash",
        "bzip2",
        "curl",
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
    config_dirs = root / "config-dirs"
    data_dirs = root / "data-dirs"

    for path in (home, config, cache, data, state, config_dirs, data_dirs):
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
        "_ARGCOMPLETE",
    ):
        env.pop(key, None)
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(config)
    env["XDG_CACHE_HOME"] = str(cache)
    env["XDG_DATA_HOME"] = str(data)
    env["XDG_STATE_HOME"] = str(state)
    env["XDG_CONFIG_DIRS"] = str(config_dirs)
    env["XDG_DATA_DIRS"] = str(data_dirs)

    # disable rich text
    env["TERM"] = "dumb"

    return env
