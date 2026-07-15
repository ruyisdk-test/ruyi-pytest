
import pexpect

from typing import Dict

from tests.helpers import (
    bind_gettext,
    env_with_blocked_network,
    ruyi_init_default_telemetry,
    spawn_ruyi,
    xfail_known_ruyi_defect,
)


def _interrupt_wizard(child: pexpect.spawn, env: Dict[str, str]) -> None:
    _ = bind_gettext(env, {
        "zh_CN.UTF-8": {
            "Keyboard interrupt received, exiting.": "收到键盘中断，正在退出。",
        },
    })
    child.sendcontrol("c")
    child.expect_exact(_("Keyboard interrupt received, exiting."))
    child.expect(pexpect.EOF)


def _assert_wizard_interrupted(child: pexpect.spawn, ruyi_version: str) -> None:
    assert child.exitstatus == 1 or (
        ruyi_version == "0.50.0-beta.20260623" and child.exitstatus == 0
    )


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
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Exiting. You can restart the wizard whenever prepared.":
                "正在退出。您可在准备好之后随时重新启动向导。",
        },
    })
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
        child.expect_exact(_("Exiting. You can restart the wizard whenever prepared."))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1


def test_ruyi_device_provision_keyboard_interrupt(
    ruyi_exe: str,
    ruyi_version: str,
    isolated_env: Dict[str, str],
):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Keyboard interrupt received, exiting.": "收到键盘中断，正在退出。",
        },
    })
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(ruyi_exe, ["device", "provision"], env=isolated_env)
    try:
        child.expect(r"\(y/N\)")
        child.sendcontrol("c")
        child.expect_exact(_("Keyboard interrupt received, exiting."))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    if child.exitstatus == 0:
        xfail_known_ruyi_defect(
            ruyi_version,
            ("0.50.0-beta.20260623",),
            "the device wizard handles Ctrl-C but exits with status 0",
        )
    assert child.exitstatus == 1


def test_ruyi_device_provision(
    ruyi_exe: str,
    ruyi_version: str,
    isolated_env: Dict[str, str],
):
    """测试 `ruyi device provision` 命令：取消（n）和进入向导（y）。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Please pick your device": "请选择您的设备",
            "Exiting. You can restart the wizard whenever prepared.":
                "正在退出。您可在准备好之后随时重新启动向导。",
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
        child.expect_exact(_("Exiting. You can restart the wizard whenever prepared."))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 1

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
        _interrupt_wizard(child, isolated_env)
    finally:
        child.close()
    assert _("Please pick your device") in output
    _assert_wizard_interrupted(child, ruyi_version)


def test_ruyi_device_provision_select(
    ruyi_exe: str,
    ruyi_version: str,
    isolated_env: Dict[str, str],
):
    """测试 `ruyi device provision`：选择设备后进入下一阶段（变体选择）。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Please pick your device": "请选择您的设备",
            "The device has the following variants. Please choose the one corresponding to your hardware at hand:":
                "该设备有以下变体。请选择与您手头硬件对应的变体：",
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
        child.expect_exact(_("The device has the following variants. Please choose the one corresponding to your hardware at hand:"))
        child.expect(r"\(\d+-\d+\)")
        _interrupt_wizard(child, isolated_env)
    finally:
        child.close()

    assert _("Please pick your device") in output_device
    _assert_wizard_interrupted(child, ruyi_version)


def test_ruyi_device_provision_invalid_selection(
    ruyi_exe: str,
    ruyi_version: str,
    isolated_env: Dict[str, str],
):
    """测试 `ruyi device provision`：选择无效设备号后应提示错误并重新要求输入。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Out-of-range input '9999'.": "输入 '9999' 超出了范围。",
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
        child.sendline("9999")
        child.expect_exact(_("Out-of-range input '9999'."))
        child.expect(r"\(\d+-\d+\)")
        _interrupt_wizard(child, isolated_env)
    finally:
        child.close()
    _assert_wizard_interrupted(child, ruyi_version)


def test_ruyi_device_provision_variant_system_select(
    ruyi_exe: str, isolated_env: Dict[str, str]
):
    """测试 `ruyi device provision`：选完设备后，继续选变体→选系统→确认下载 的完整流程。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "The device has the following variants. Please choose the one corresponding to your hardware at hand:":
                "该设备有以下变体。请选择与您手头硬件对应的变体：",
            "The following system configurations are supported by the device variant you have chosen. Please pick the one you want to put on the device:":
                "您选择的设备变体支持以下系统配置。请选择您想要安装到设备上的配置：",
            "We are about to download and install the following packages for your device:":
                "我们即将为您的设备下载并安装以下软件包：",
        },
    })
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
        child.expect_exact(_("The device has the following variants. Please choose the one corresponding to your hardware at hand:"))
        child.expect(r"\(\d+-\d+\)")
        child.sendline("1")

        # Step 4: select system configuration
        child.expect_exact(_("The following system configurations are supported by the device variant you have chosen. Please pick the one you want to put on the device:"))
        child.expect(r"\(\d+-\d+\)")
        child.sendline("1")

        # Step 5: download confirmation
        child.expect_exact(_("We are about to download and install the following packages for your device:"))
        child.expect(r"\(y/N\)")
        child.sendline("n")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1  # cancelled download


def test_ruyi_device_provision_invalid_variant(
    ruyi_exe: str,
    ruyi_version: str,
    isolated_env: Dict[str, str],
):
    """测试 `ruyi device provision`：在变体选择阶段输入无效编号后应提示错误并重新要求输入。"""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Out-of-range input '9999'.": "输入 '9999' 超出了范围。",
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
        child.sendline("1")
        child.expect(r"\(\d+-\d+\)")  # step 3: variant list
        child.sendline("9999")
        child.expect_exact(_("Out-of-range input '9999'."))
        child.expect(r"\(\d+-\d+\)")
        _interrupt_wizard(child, isolated_env)
    finally:
        child.close()
    _assert_wizard_interrupted(child, ruyi_version)


def test_ruyi_device_provision_invalid_system(
    ruyi_exe: str,
    ruyi_version: str,
    isolated_env: Dict[str, str],
):
    """测试 `ruyi device provision`：在系统配置选择阶段输入无效编号后应提示错误并重新要求输入。"""
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "Out-of-range input '9999'.": "输入 '9999' 超出了范围。",
        },
    })

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
        child.expect_exact(_("Out-of-range input '9999'."))
        child.expect(r"\(\d+-\d+\)")
        _interrupt_wizard(child, isolated_env)
    finally:
        child.close()
    _assert_wizard_interrupted(child, ruyi_version)


def test_ruyi_device_provision_download_failure_does_not_touch_device(
    ruyi_exe: str,
    ruyi_version: str,
    ruyi_dep: bool,
    isolated_env: Dict[str, str],
):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "fatal error: failed to download and install packages":
                "致命错误：下载和安装软件包失败",
            "info: your device was not touched": "信息：您的设备未受任何操作",
            "Downloads can fail for a multitude of reasons": "下载可能因各种原因失败，",
        },
    })
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    failed_env = env_with_blocked_network(isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["device", "provision"],
        env=failed_env,
        timeout=10 * 60,
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
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()

    assert _("Downloads can fail for a multitude of reasons") in output
    failed_message = _("fatal error: failed to download and install packages")
    untouched_message = _("info: your device was not touched")
    if failed_message not in output and untouched_message not in output:
        assert child.exitstatus == 1
        xfail_known_ruyi_defect(
            ruyi_version,
            ("0.50.0-beta.20260623", "0.51.0-alpha.20260616"),
            "the downloader exits before the device wizard reports that the device was untouched",
        )
    assert failed_message in output
    assert untouched_message in output
    assert child.exitstatus == 2
