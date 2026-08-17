# ruyi-pytest

Successor of [ruyi-litester](https://github.com/ruyisdk-test/ruyi-litester).

`ruyi-pytest` is an integration test suite for validating that the `ruyi` command-line interface works as expected. The suite focuses on command behavior, exit status, generated files, installed packages, virtual environments, package execution, and user-visible output in both English and Chinese locales.

## Requirements

The test runner expects Ruyi **0.51.0-beta.20260714 or newer** to be available as `ruyi` in `PATH`. Ruyi is intentionally not installed as a Python development dependency, so `uv run` cannot silently replace the executable under test with a different PyPI version.

The suite targets Linux. Some tests download packages and require common archive tools. `conftest.py` checks for the required commands, including `bash`, `bzip2`, `curl`, `gunzip`, `lz4`, `tar`, `xz`, `zstd`, and `unzip`. Toolchain build tests also require `make`.

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

Recalculate the source-level test point count:

```bash
python scripts/count_test_points.py
```

The current suite collects **58 pytest test cases**.

The source currently contains **973 assertion-level checks**, including **5 checks in shared helpers**, or **1,946 bilingual test points** across the two locale runs. The script counts each `assert` statement and each `pexpect.expect*` call once, including EOF checks. Shared helper bodies are counted once rather than expanded at every call site. It does not expand loops, architecture branches, or locale runs. The bilingual total therefore represents the written test surface; the exact number executed can vary by host architecture because some package tests are platform-gated.

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
| Top-level CLI/version | `tests/basic/test_ruyi_version.py` | root help, `version`, `-V`, `--version`, `--porcelain version`, invalid subcommand, side-effect-free version queries |
| Completion | `tests/basic/test_ruyi_completion.py` | both completion-script argument forms, bash/zsh output, unsupported shell, live bash completion, first-run side effects |
| Admin | `tests/basic/test_ruyi_admin.py` | exact checksums and sizes, multiple files, restrictions, install size, manifest formatting, file/repo checks, selectors, porcelain diagnostics, build argument/error paths, missing plugin command |
| Config | `tests/basic/test_ruyi_config.py` | `get`, `set`, `unset`, `remove-section`, invalid keys, invalid values, protected config, missing argument |
| Repo | `tests/basic/test_ruyi_repo.py` | lifecycle, remote/local repos, branch/name/priority persistence, porcelain output, validation errors, cached purge, external-path safety contract |
| Update/news | `tests/basic/test_ruyi_news.py` | `update`, selected/invalid repo, bare `news`, all/new lists, ID/ordinal/quiet reads, persisted read state, porcelain JSONL |
| Entity (experimental) | `tests/basic/test_ruyi_entity.py` | feature gate, list/type filter, describe success/error, relationships, porcelain JSONL, package relation filter, repeated-filter contract |
| Telemetry | `tests/basic/test_ruyi_telemetry.py` | all modes and aliases, plain/verbose status, upload invocation, invalid subcommand, persistence |
| Install | `tests/basic/test_ruyi_install.py` | download failure/retry, install, successful reinstall, version atoms, source/binary fetch-only contracts, alias `i`, multiple atoms, host override |
| Uninstall | `tests/basic/test_ruyi_uninstall.py` | nonexistent package, host isolation, interactive cancel/confirm, `-y`, aliases `remove` and `rm` |
| Extract | `tests/basic/test_ruyi_extract.py` | default/subdirless extraction, destination, fetch-only side effects, host error, nonexistent package |
| List | `tests/basic/test_ruyi_list.py` | no-filter contract, `--all`, verbose/details, installed/category/name filters, unavailable packages, porcelain JSONL, profiles |
| Venv | `tests/basic/test_ruyi_venv.py` | GNU/LLVM/emulator venvs, activation/name/deactivation, compilation/execution, all sysroot modes, option validation, canonical package sysroot option, real extra command via `wlink` |
| Self | `tests/basic/test_ruyi_self.py` | every clean selector, quiet mode, external-repo protection, `--all`, safe cancellation or installation-form rejection of normal and `--purge` uninstall |
| Device | `tests/basic/test_ruyi_device.py` | help, `flash` alias, wizard stages, concrete invalid-selection diagnostics, cancellation, interrupt and download-failure safety contracts; never real flashing |
| Toolchain packages | `tests/packages/test_ruyi_toolchain.py` | selected toolchain installation, venv creation, compilation, object inspection, qemu execution where applicable |
| Emulator packages | `tests/packages/test_ruyi_emulator.py` | selected emulator packages, generated ELF execution, qemu/binfmt-style behavior where applicable |

## Current test count

Current collected pytest tests by file:

| Test file | Pytest cases | Bilingual test points |
| --- | ---: | ---: |
| `tests/basic/test_ruyi_admin.py` | 7 | 174 |
| `tests/basic/test_ruyi_completion.py` | 2 | 56 |
| `tests/basic/test_ruyi_config.py` | 2 | 104 |
| `tests/basic/test_ruyi_device.py` | 10 | 124 |
| `tests/basic/test_ruyi_entity.py` | 2 | 76 |
| `tests/basic/test_ruyi_extract.py` | 2 | 78 |
| `tests/basic/test_ruyi_install.py` | 4 | 154 |
| `tests/basic/test_ruyi_list.py` | 3 | 154 |
| `tests/basic/test_ruyi_news.py` | 1 | 124 |
| `tests/basic/test_ruyi_repo.py` | 5 | 174 |
| `tests/basic/test_ruyi_self.py` | 3 | 88 |
| `tests/basic/test_ruyi_telemetry.py` | 2 | 100 |
| `tests/basic/test_ruyi_uninstall.py` | 2 | 140 |
| `tests/basic/test_ruyi_venv.py` | 3 | 208 |
| `tests/basic/test_ruyi_version.py` | 2 | 34 |
| `tests/packages/test_ruyi_emulator.py` | 4 | 56 |
| `tests/packages/test_ruyi_toolchain.py` | 4 | 92 |
| **Test files total** | **58** | **1,936** |
| Shared helpers (`tests/helpers.py`) | - | **10** |
| **Bilingual total** | **58** | **1,946** |

The table above reports bilingual points per test file. The source-level count is 968 points in test files plus 5 shared-helper points, for 973 points per locale and 1,946 bilingual points. The script output is authoritative if this table changes.

The test-point column is the bilingual total. The source-level count does not expand loops or architecture branches; actual executed checks therefore vary by host architecture and runtime branch.

## Historical regression contracts

Five tests retain behavior-scoped handling for defects confirmed in older Ruyi 0.50 beta or 0.51 alpha builds. The supported Ruyi 0.51 beta behavior is expected to pass these contracts. Each historical defect has an explicit affected-version allowlist, so observing it on a supported or otherwise unlisted Ruyi version is a hard failure.

| Contract | Historical defect |
| --- | --- |
| Device wizard Ctrl-C | The interrupt message is printed, but the packaged binary exits with status 0 instead of 1. |
| Device download failure | The downloader exits before the wizard can report that the device was not touched. |
| Repeated entity-type filters | `entity list` processes only the first repeated `--entity-type`. |
| Binary install fetch-only | `install --fetch-only` creates an empty installation root. |
| External local repo purge | `repo remove --purge` deletes the externally managed path configured with `--local`. |

## Known intentional gaps

The suite intentionally does not fully exercise some paths:

- Real `device provision` flashing or disk writing is not performed.
- Real `ruyi self uninstall -y` is not performed because it can remove the `ruyi` binary. The normal and `--purge` forms are covered through safe cancellation for standalone binaries and safe rejection for externally managed or non-standalone binaries.
- Successful `admin build-package` and successful plugin command execution are not covered because they require dedicated recipe/plugin fixtures.
- The suite does not attempt a Cartesian product of all packages, profiles, hosts, and argument combinations. It covers representative paths for each command area instead.
- Full network failure matrices, corrupted cache recovery, and corrupted repository recovery are not exhaustively tested.

## Notes for contributors

When adding tests:

- Prefer isolated environments through the existing `isolated_env` fixture.
- Keep tests locale-aware when asserting translated output.
- Avoid root-only behavior and avoid modifying files outside the project directory, except pytest temporary directories.
- Do not run destructive `self uninstall` paths against the `ruyi` binary from `PATH`; test only safe cancellation or isolated behavior.
- Mark known upstream defects only after verifying unaffected behavior, and keep an explicit affected-version allowlist so newer Ruyi versions must either pass or surface a regression.
- Prefer representative command paths over combinatorial argument matrices.
