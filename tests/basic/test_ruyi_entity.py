import json
import pexpect

from typing import Dict

from tests.helpers import (
    bind_gettext,
    ruyi_init_default_telemetry,
    spawn_ruyi,
)


def test_ruyi_entity_queries_and_feature_gate(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Entity device:milkv-duo (Milk-V Duo)": "实体 device:milkv-duo（Milk-V Duo）",
            "  Direct forward relationships:": "  直接正向关系：",
            "  Direct reverse relationships:": "  直接反向关系：",
            "  All indirectly related entities:": "  所有间接相关的实体：",
            "fatal error: entity no-such-type:no-such-entity not found":
                "致命错误：未找到实体 no-such-type:no-such-entity",
            "List of available packages:": "可用软件包列表：",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(ruyi_exe, ["--help"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert "entity" not in child.before
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["entity"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 2

    experimental_env = isolated_env.copy()
    experimental_env["RUYI_EXPERIMENTAL"] = "1"

    child = spawn_ruyi(
        ruyi_exe,
        ["entity", "list", "--entity-type", "device"],
        env=experimental_env,
    )
    try:
        child.expect_exact("'device:milkv-duo':")
        child.expect_exact("display name: Milk-V Duo")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["entity", "describe", "device:milkv-duo"],
        env=experimental_env,
    )
    try:
        child.expect_exact(_("Entity device:milkv-duo (Milk-V Duo)"))
        child.expect_exact(_("  Direct forward relationships:"))
        child.expect_exact("device-variant:milkv-duo@256m")
        child.expect_exact("device-variant:milkv-duo@64m")
        child.expect_exact(_("  Direct reverse relationships:"))
        child.expect_exact(_("  All indirectly related entities:"))
        child.expect_exact("cpu:generic-rv64gc")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["entity", "describe", "no-such-type:no-such-entity"],
        env=experimental_env,
    )
    try:
        child.expect_exact(_("fatal error: entity no-such-type:no-such-entity not found"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

    child = spawn_ruyi(
        ruyi_exe,
        ["--porcelain", "entity", "list", "--entity-type", "device"],
        env=experimental_env,
    )
    try:
        child.expect(pexpect.EOF)
        records = [json.loads(line) for line in child.before.splitlines() if line]
    finally:
        child.close()
    assert child.exitstatus == 0
    milkv_duo = next(record for record in records if record["entity_id"] == "milkv-duo")
    assert milkv_duo["ty"] == "entitylistoutput-v1"
    assert milkv_duo["entity_type"] == "device"
    assert milkv_duo["display_name"] == "Milk-V Duo"
    assert "device-variant:milkv-duo@64m" in milkv_duo["related_refs"]

    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--related-to-entity", "arch:riscv64"],
        env=experimental_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("toolchain/gnu-plct")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0


def test_ruyi_entity_multiple_type_filter(
    ruyi_exe: str,
    isolated_env: Dict[str, str],
):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    experimental_env = isolated_env.copy()
    experimental_env["RUYI_EXPERIMENTAL"] = "1"

    child = spawn_ruyi(
        ruyi_exe,
        ["entity", "list", "--entity-type", "uarch"],
        env=experimental_env,
    )
    try:
        child.expect(pexpect.EOF)
        uarch_output = child.before
    finally:
        child.close()
    assert child.exitstatus == 0
    assert "'uarch:generic-rv64gc':" in uarch_output

    child = spawn_ruyi(
        ruyi_exe,
        [
            "entity", "list",
            "--entity-type", "device",
            "--entity-type", "uarch",
        ],
        env=experimental_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()
    assert child.exitstatus == 0
    assert "'device:milkv-duo':" in output
    assert "'uarch:generic-rv64gc':" in output
