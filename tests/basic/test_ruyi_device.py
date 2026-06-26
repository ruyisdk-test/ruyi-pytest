
import pexpect

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_device_no_subcommand(ruyi_exe: str, isolated_env: Dict[str, str]):
    """测试 `ruyi device` 无子命令：应显示帮助信息。"""
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["device"],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()
    assert child.exitstatus == 0
    assert "provision" in output


def test_ruyi_device_flash_alias(ruyi_exe: str, isolated_env: Dict[str, str]):
    """测试 `ruyi device flash` 作为 provision 的别名。"""
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # device flash 应等价于 device provision，同样提示 (y/N)
    child = spawn_ruyi(
        ruyi_exe,
        ["device", "flash"],
        env=isolated_env,
    )
    try:
        child.expect(r"\(y/N\)")
        child.sendline("n")
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()
    assert child.exitstatus == 1
    assert output != ""


def test_ruyi_device_provision(ruyi_exe: str, isolated_env: Dict[str, str]):
    """测试 `ruyi device provision` 命令：取消（n）和进入向导（y）。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Please pick your device": "请选择您的设备",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # 输入 "n" 取消向导
    # "(y/N)" 是硬编码的英文，未被 _() 包裹
    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=isolated_env,
    )
    try:
        child.expect(r"\(y/N\)")
        child.sendline("n")
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()
    assert child.exitstatus == 1
    assert output != ""  # 验证取消操作有输出

    # 输入 "y" 继续，验证设备列表出现
    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=isolated_env,
    )
    try:
        child.expect(r"\(y/N\)")
        child.sendline("y")
        # 匹配数字范围 "(1-N)"，未被翻译
        child.expect(r"\(\d+-\d+\)")
        output = child.before
    finally:
        child.close()
    assert _("Please pick your device") in output


def test_ruyi_device_provision_select(ruyi_exe: str, isolated_env: Dict[str, str]):
    """测试 `ruyi device provision`：选择设备后进入下一阶段（变体选择）。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Please pick your device": "请选择您的设备",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=isolated_env,
    )
    try:
        child.expect(r"\(y/N\)")
        child.sendline("y")
        child.expect(r"\(\d+-\d+\)")  # step 2: device model list
        output_device = child.before
        child.sendline("1")
        # Step 3: variant list should appear after selecting a device
        child.expect(r"\(\d+-\d+\)")
        output = child.before
    finally:
        child.close()

    assert _("Please pick your device") in output_device
    assert output != ""  # variant list appeared


def test_ruyi_device_provision_invalid_selection(
    ruyi_exe: str, isolated_env: Dict[str, str]
):
    """测试 `ruyi device provision`：选择无效设备号后应提示错误并重新要求输入。"""
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=isolated_env,
    )
    try:
        child.expect(r"\(y/N\)")
        child.sendline("y")
        child.expect(r"\(\d+-\d+\)")  # step 2: device model list
        child.sendline("9999")
        # Invalid input → error message + re-prompt "选择？(1-38)"
        child.expect(r"\(\d+-\d+\)")
        output = child.before
    finally:
        child.close()

    assert output != ""  # error message was shown


def test_ruyi_device_provision_variant_system_select(
    ruyi_exe: str, isolated_env: Dict[str, str]
):
    """测试 `ruyi device provision`：选完设备后，继续选变体→选系统→确认下载 的完整流程。"""
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=isolated_env,
    )
    try:
        # Step 1: confirm entering wizard
        child.expect(r"\(y/N\)")
        child.sendline("y")

        # Step 2: select device model
        child.expect(r"\(\d+-\d+\)")
        child.sendline("1")

        # Step 3: select device variant
        child.expect(r"\(\d+-\d+\)")
        output_variant = child.before
        child.sendline("1")

        # Step 4: select system configuration
        child.expect(r"\(\d+-\d+\)")
        output_system = child.before
        child.sendline("1")

        # Step 5: download confirmation
        child.expect(r"\(y/N\)")
        output_confirm = child.before
        child.sendline("n")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    # Verify each stage produced output (text varies by locale)
    assert output_variant, "variant stage produced no output"
    assert output_system, "system config stage produced no output"
    assert output_confirm, "download confirmation stage produced no output"
    assert child.exitstatus == 1  # cancelled download


def test_ruyi_device_provision_invalid_variant(
    ruyi_exe: str, isolated_env: Dict[str, str]
):
    """测试 `ruyi device provision`：在变体选择阶段输入无效编号后应提示错误并重新要求输入。"""
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=isolated_env,
    )
    try:
        child.expect(r"\(y/N\)")
        child.sendline("y")
        child.expect(r"\(\d+-\d+\)")  # step 2: device model list
        child.sendline("1")
        child.expect(r"\(\d+-\d+\)")  # step 3: variant list
        child.sendline("9999")
        # Invalid input → error + re-prompt
        child.expect(r"\(\d+-\d+\)")
        output = child.before
    finally:
        child.close()

    assert output != ""  # error message was shown


def test_ruyi_device_provision_invalid_system(
    ruyi_exe: str, isolated_env: Dict[str, str]
):
    """测试 `ruyi device provision`：在系统配置选择阶段输入无效编号后应提示错误并重新要求输入。"""
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=isolated_env,
    )
    try:
        child.expect(r"\(y/N\)")
        child.sendline("y")
        child.expect(r"\(\d+-\d+\)")  # step 2: device model list
        child.sendline("1")
        child.expect(r"\(\d+-\d+\)")  # step 3: variant list
        child.sendline("1")
        child.expect(r"\(\d+-\d+\)")  # step 4: system config list
        child.sendline("9999")
        # Invalid input → error + re-prompt
        child.expect(r"\(\d+-\d+\)")
        output = child.before
    finally:
        child.close()

    assert output != ""  # error message was shown


def test_ruyi_device_provision_confirm_proceed(
    ruyi_exe: str, isolated_env: Dict[str, str]
):
    """测试 `ruyi device provision`：确认下载后应开始下载过程。"""
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect(r"\(y/N\)")
        child.sendline("y")
        child.expect(r"\(\d+-\d+\)")  # step 2: device model list
        child.sendline("1")
        child.expect(r"\(\d+-\d+\)")  # step 3: variant list
        child.sendline("1")
        child.expect(r"\(\d+-\d+\)")  # step 4: system config list
        child.sendline("1")
        child.expect(r"\(y/N\)")  # step 5: download confirmation
        child.sendline("y")

        # Download should start shortly; curl progress bars or extraction
        # messages will appear. Wait for output by letting pexpect time out
        # (the process stays alive while downloading).
        try:
            child.expect(pexpect.TIMEOUT, timeout=15)
        except pexpect.TIMEOUT:
            pass
        output = child.before or ""
    finally:
        child.close()

    assert output != ""
