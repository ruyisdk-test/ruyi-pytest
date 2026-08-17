#!/usr/bin/env python3
"""Count assertion-level checks in the Ruyi integration test suite.

The report uses a source-level metric:

* every ``assert`` statement counts as one point;
* every ``pexpect`` ``expect*`` call counts as one point, including EOF
  checks;
* checks in ``tests/helpers.py`` are counted separately and included in the
  total because test cases exercise those shared helpers. Helper bodies are
  counted once; call-site expansion is intentionally not attempted.

The script deliberately does not expand loops, architecture branches, or
locale runs.  It reports the checks written in the source once, then derives
the bilingual total by multiplying the source total by two.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileStats:
    path: Path
    test_cases: int
    assertions: int
    expect_calls: int

    @property
    def source_points(self) -> int:
        return self.assertions + self.expect_calls


def _is_expect_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr.startswith("expect")
    )


def _count_file(path: Path, *, test_files_only: bool) -> FileStats:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    test_cases = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
        for node in ast.walk(tree)
    )
    assertions = sum(isinstance(node, ast.Assert) for node in ast.walk(tree))
    expect_calls = sum(_is_expect_call(node) for node in ast.walk(tree))

    if test_files_only:
        return FileStats(path, test_cases, assertions, expect_calls)
    return FileStats(path, 0, assertions, expect_calls)


def collect_stats(root: Path) -> tuple[list[FileStats], FileStats | None]:
    test_files = sorted(root.glob("tests/**/test_*.py"))
    stats = [_count_file(path, test_files_only=True) for path in test_files]

    helper_path = root / "tests" / "helpers.py"
    helper_stats = (
        _count_file(helper_path, test_files_only=False)
        if helper_path.is_file()
        else None
    )
    return stats, helper_stats


def _print_table(
    root: Path,
    stats: list[FileStats],
    helper_stats: FileStats | None,
) -> None:
    print(
        "| Test file | Pytest cases | assert | expect* | "
        "Source points | Bilingual points |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for item in stats:
        relative_path = item.path.relative_to(root).as_posix()
        print(
            f"| `{relative_path}` | {item.test_cases} | {item.assertions} | "
            f"{item.expect_calls} | {item.source_points} | "
            f"{item.source_points * 2} |"
        )

    test_cases = sum(item.test_cases for item in stats)
    assertions = sum(item.assertions for item in stats)
    expect_calls = sum(item.expect_calls for item in stats)
    source_points = assertions + expect_calls
    print(
        f"| **Test files total** | **{test_cases}** | **{assertions}** | "
        f"**{expect_calls}** | **{source_points}** | "
        f"**{source_points * 2}** |"
    )

    helper_points = helper_stats.source_points if helper_stats else 0
    print(
        f"| Shared helpers (`tests/helpers.py`) | - | "
        f"{helper_stats.assertions if helper_stats else 0} | "
        f"{helper_stats.expect_calls if helper_stats else 0} | "
        f"{helper_points} | {helper_points * 2} |"
    )
    print()
    print(f"Pytest cases: {test_cases}")
    print(f"Test-file source points: {source_points}")
    print(f"Shared-helper points: {helper_points}")
    print(f"Source points including helpers: {source_points + helper_points}")
    print(f"Bilingual points: {(source_points + helper_points) * 2}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="project root (default: directory containing scripts/)",
    )
    args = parser.parse_args()

    stats, helper_stats = collect_stats(args.root.resolve())
    _print_table(args.root.resolve(), stats, helper_stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
