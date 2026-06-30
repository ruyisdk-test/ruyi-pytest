
import pexpect

from typing import Dict

from tests.helpers import bind_gettext, ruyi_config_iscas_mirror, spawn_ruyi


def test_ruyi_update_telemetry_no(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            " new news item(s):": "条新的新闻条目：",
            "No.": "序号",
            "Title": "标题",
            "You can read them with ruyi news read.": "您可以使用 ruyi news read 阅读它们",
        },
    })

    # ruyi update (first run, telemetry prompt → answer no)
    child = spawn_ruyi(
        ruyi_exe,
        ["update"],
        env=isolated_env,
        timeout=60,
    )
    try:
        while True:
            idx = child.expect(["(y/N)", pexpect.EOF])
            if idx == 0:
                child.sendline("")  # default N
            else:
                break
    finally:
        child.close()
    assert child.exitstatus == 0

    # ruyi update (second run, already initialized, no prompt)
    child = spawn_ruyi(
        ruyi_exe,
        ["update"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0


def test_ruyi_update_telemetry_yes(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "info: telemetry data uploading is now enabled": "信息：现已启用遥测数据上传",
            " new news item(s):": "条新的新闻条目：",
            "No.": "序号",
            "Title": "标题",
            "You can read them with ruyi news read.": "您可以使用 ruyi news read 阅读它们",
        },
    })

    # ruyi update (first run, telemetry prompt → answer yes)
    child = spawn_ruyi(
        ruyi_exe,
        ["update"],
        env=isolated_env,
        timeout=60,
    )
    try:
        while True:
            idx = child.expect(["(y/N)", pexpect.EOF])
            if idx == 0:
                child.sendline("y")
            else:
                break
    finally:
        child.close()
    assert child.exitstatus == 0
    assert _("info: telemetry data uploading is now enabled") in child.before

    # ruyi update (second run, already initialized, no prompt)
    child = spawn_ruyi(
        ruyi_exe,
        ["update"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
