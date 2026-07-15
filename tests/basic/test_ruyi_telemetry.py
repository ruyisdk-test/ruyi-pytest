
import pexpect

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_telemetry_modes(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    """Test `ruyi telemetry` mode switching: status, optout/off, consent/on, local, and persistence."""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "info: telemetry data collection is now disabled": "信息：现已禁用遥测数据收集",
            "info: telemetry data uploading is now enabled": "信息：现已启用遥测数据上传",
            "info: telemetry mode is now set to local collection only": "信息：遥测模式现已设置为仅本地收集",
            "info: telemetry mode is off: nothing is collected or uploaded after the first run":
                "信息：遥测模式为 off：首次运行后，不会收集或上传任何内容",
            "info: telemetry mode is local: local usage collection only, no usage uploads except if requested":
                "信息：遥测模式为 local：仅本地使用收集，除非明确请求否则不会上传",
            "info: telemetry mode is on: usage data is collected and periodically uploaded":
                "信息：遥测模式为 on：使用数据会被收集并定期上传",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # status: initial state should be valid
    child = spawn_ruyi(ruyi_exe, ["telemetry", "status"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert child.before.strip() in (_("on"), _("off"), _("local"))
    finally:
        child.close()
    assert child.exitstatus == 0

    # consent: enable uploads (off → on, most likely crosses boundary)
    child = spawn_ruyi(ruyi_exe, ["telemetry", "consent"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry data uploading is now enabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert child.before.strip() == "on"
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status", "--verbose"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry mode is on: usage data is collected and periodically uploaded"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # optout: disable data collection (on → off, proves optout works)
    child = spawn_ruyi(ruyi_exe, ["telemetry", "optout"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry data collection is now disabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status", "-v"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry mode is off: nothing is collected or uploaded after the first run"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert child.before.strip() == "off"
    finally:
        child.close()
    assert child.exitstatus == 0

    # on alias: same as consent (off → on, proves alias works)
    child = spawn_ruyi(ruyi_exe, ["telemetry", "on"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry data uploading is now enabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert child.before.strip() == "on"
    finally:
        child.close()
    assert child.exitstatus == 0

    # off alias: same as optout (on → off, proves alias works)
    child = spawn_ruyi(ruyi_exe, ["telemetry", "off"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry data collection is now disabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert child.before.strip() == "off"
    finally:
        child.close()
    assert child.exitstatus == 0

    # local: local collection only (off → local)
    child = spawn_ruyi(ruyi_exe, ["telemetry", "local"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry mode is now set to local collection only"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert child.before.strip() == "local"
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status", "--verbose"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry mode is local: local usage collection only, no usage uploads except if requested"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    # persistence: cycle back to optout (local → off)
    child = spawn_ruyi(ruyi_exe, ["telemetry", "optout"], env=isolated_env)
    try:
        child.expect_exact(_("info: telemetry data collection is now disabled"))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(ruyi_exe, ["telemetry", "status"], env=isolated_env)
    try:
        child.expect(pexpect.EOF)
        assert child.before.strip() == "off"
    finally:
        child.close()
    assert child.exitstatus == 0


def test_ruyi_telemetry_upload(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    """Test `ruyi telemetry upload` runs (may fail due to network)."""
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "uploaded": "已上传",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["telemetry", "upload"],
        env=isolated_env,
        timeout=30,
    )
    try:
        # upload may succeed ("info: uploaded ...") or fail with a network
        # timeout; both are acceptable in a test environment
        idx = child.expect([pexpect.EOF, _("uploaded"), pexpect.TIMEOUT], timeout=30)
        # if we hit a network timeout (pexpect.TIMEOUT), that's acceptable
    finally:
        child.close()
    # accept exit status 0 (success) or 1 (network error)
    assert child.exitstatus in (0, 1)
