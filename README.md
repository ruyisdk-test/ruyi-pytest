# ruyi-pytest

Successor of [ruyi-litester](https://github.com/ruyisdk-test/ruyi-litester).

`ruyi-pytest` is an integration test suite for validating that the `ruyi` command-line interface works as expected. The suite focuses on command behavior, exit status, generated files, installed packages, virtual environments, package execution, and user-visible output in both English and Chinese locales.

## Requirements

The test runner expects `ruyi` to be available in `PATH`.

Some tests download packages and require common archive tools. `conftest.py` checks for the required commands, including `bash`, `bzip2`, `gunzip`, `lz4`, `tar`, `xz`, `zstd`, and `unzip`. Toolchain build tests also require `make`; device provisioning tests require additional flashing tools.

The suite does not require root privileges for normal test runs. Tests use isolated `HOME` and XDG directories under pytest temporary directories. Device provisioning tests only exercise the interactive flow and do not perform real flashing.

## Run tests

Run the full suite:

```bash
uv run pytest
```

Run a subset:

```bash
uv run pytest tests/basic/test_ruyi_repo.py
uv run pytest tests/basic/test_ruyi_install.py::test_ruyi_install_fetch_reinstall_and_alias
```

Collect tests without executing them:

```bash
uv run pytest --collect-only -q
```

The current suite collects **47 pytest test cases**.

At assertion-level granularity, the suite currently covers about **849 test points**. A test point is counted for each explicit comparison against `ruyi`'s actual output text, exit status, or return value. Locale-aware checks are counted separately for English and Chinese runs, so the same output/return-value check in `en_US.UTF-8` and `zh_CN.UTF-8` counts as two test points. The exact number executed can vary by host architecture because some package tests are platform-gated.

## Locale coverage

The test suite supports English and Chinese output. Use `LANG` to select the locale:

```bash
LANG=en_US.UTF-8 uv run pytest
LANG=zh_CN.UTF-8 uv run pytest
```

Many tests use locale-aware assertions through `tests.helpers.bind_gettext`, so expected messages are checked in both languages where the command output is translated.

## Choose packages-index mirror

Create `.env` to select a packages-index mirror.

ISCAS mirror:

```bash
RUYI_REPO=ISCAS
```

Gitee mirror (unofficial):

```bash
RUYI_REPO=GITEE
```

In network environments where the default upstream packages-index is slow or inaccessible, `RUYI_REPO=ISCAS` is recommended.

## Test coverage summary

This is an integration test suite, not a Python line-coverage suite. Coverage is measured by `ruyi` command surface and user-visible behavior.

The current tests cover all major test-worthy `ruyi` CLI command groups except destructive or hardware-dependent real execution paths.

Covered command areas:

| Area | Test file(s) | Coverage |
| --- | --- | --- |
| Top-level CLI/version | `tests/basic/test_ruyi_version.py` | `version`, `-V`, `--version`, `--porcelain version`, invalid top-level subcommand |
| Completion | `tests/basic/test_ruyi_completion.py` | completion script output, bash completion behavior |
| Admin | `tests/basic/test_ruyi_admin.py` | `checksum`, `format-manifest`, `check`, `build-package --dry-run` error path, missing plugin command path |
| Config | `tests/basic/test_ruyi_config.py` | `get`, `set`, `unset`, `remove-section`, invalid keys, invalid values, protected config, missing argument |
| Repo | `tests/basic/test_ruyi_repo.py` | `list`, `add`, `remove`, `enable`, `disable`, `set-priority`, duplicate repo, missing repo, invalid priority |
| Update/news | `tests/basic/test_ruyi_news.py` | `update`, `update --repo`, invalid repo, `news list`, `news list --new`, `news read`, invalid news ID/ordinal |
| Telemetry | `tests/basic/test_ruyi_telemetry.py` | `status`, `consent`, `on`, `optout`, `off`, `local`, `upload`, invalid telemetry subcommand |
| Install | `tests/basic/test_ruyi_install.py` | install success, download failure, version specifiers, `-f/--fetch-only`, `--reinstall` error path, alias `i`, multiple atoms, `--host` |
| Uninstall | `tests/basic/test_ruyi_uninstall.py` | nonexistent package, interactive cancel/confirm, `-y`, aliases `remove` and `rm` |
| Extract | `tests/basic/test_ruyi_extract.py` | default extraction, `--extract-without-subdir`, `-d/--dest-dir`, `-f/--fetch-only`, nonexistent package |
| List | `tests/basic/test_ruyi_list.py` | package listing, `--verbose`, `--is-installed`, `--category-is`, `--category-contains`, unavailable packages, `list profiles` |
| Venv | `tests/basic/test_ruyi_venv.py` | toolchain venvs, emulator venvs, activation/deactivation, sysroot from package, `--without-sysroot`, copied/symlinked/projected sysroot, `--extra-commands-from`, missing destination |
| Self | `tests/basic/test_ruyi_self.py` | `self clean`, no-data clean error, safe interactive cancellation of `self uninstall` |
| Device | `tests/basic/test_ruyi_device.py` | `device` help flow, `flash` alias, interactive `provision` wizard paths and invalid selections |
| Toolchain packages | `tests/packages/test_ruyi_toolchain.py` | selected toolchain installation, venv creation, compilation, object inspection, qemu execution where applicable |
| Emulator packages | `tests/packages/test_ruyi_emulator.py` | selected emulator packages, generated ELF execution, qemu/binfmt-style behavior where applicable |

## Current test count

Current collected pytest tests by file:

| Test file | Pytest cases | Assertion-level test points |
| --- | ---: | ---: |
| `tests/basic/test_ruyi_admin.py` | 4 | 26 |
| `tests/basic/test_ruyi_completion.py` | 2 | 29 |
| `tests/basic/test_ruyi_config.py` | 2 | 30 |
| `tests/basic/test_ruyi_device.py` | 9 | 57 |
| `tests/basic/test_ruyi_extract.py` | 2 | 32 |
| `tests/basic/test_ruyi_install.py` | 3 | 90 |
| `tests/basic/test_ruyi_list.py` | 2 | 96 |
| `tests/basic/test_ruyi_news.py` | 1 | 86 |
| `tests/basic/test_ruyi_repo.py` | 2 | 47 |
| `tests/basic/test_ruyi_self.py` | 2 | 22 |
| `tests/basic/test_ruyi_telemetry.py` | 3 | 57 |
| `tests/basic/test_ruyi_uninstall.py` | 2 | 90 |
| `tests/basic/test_ruyi_venv.py` | 3 | 112 |
| `tests/basic/test_ruyi_version.py` | 2 | 19 |
| `tests/packages/test_ruyi_emulator.py` | 4 | 24 |
| `tests/packages/test_ruyi_toolchain.py` | 4 | 32 |
| **Total** | **47** | **849** |

## Known intentional gaps

The suite intentionally does not fully exercise some paths:

- Real `device provision` flashing or disk writing is not performed.
- Real `ruyi self uninstall -y` or `ruyi self uninstall --purge` is not performed because it can remove the `ruyi` binary or user-managed data.
- Successful `admin build-package` and successful plugin command execution are not covered because they require dedicated recipe/plugin fixtures.
- The suite does not attempt a Cartesian product of all packages, profiles, hosts, and argument combinations. It covers representative paths for each command area instead.
- Full network failure matrices, corrupted cache recovery, and corrupted repository recovery are not exhaustively tested.

## Notes for contributors

When adding tests:

- Prefer isolated environments through the existing `isolated_env` fixture.
- Keep tests locale-aware when asserting translated output.
- Avoid root-only behavior and avoid modifying files outside the project directory, except pytest temporary directories.
- Do not run destructive `self uninstall` paths against the `ruyi` binary from `PATH`; test only safe cancellation or isolated behavior.
- Prefer representative command paths over combinatorial argument matrices.
