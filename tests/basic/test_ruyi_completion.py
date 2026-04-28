import pexpect

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_output_completion_script(ruyi_exe: str, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "ruyi: error: argument --output-completion-script: expected one argumen":
                "ruyi：错误：参数 --output-completion-script: 预期单个参数",
        },
    })

    # TODO:
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    child = spawn_ruyi(
        ruyi_exe,
        ["--output-completion-script"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("ruyi: error: argument --output-completion-script: expected one argumen"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 2

    child = spawn_ruyi(
        ruyi_exe,
        ["--output-completion-script=bash"],
        env=isolated_env,
    )
    try:
        child.expect_exact("#compdef ruyi")
        child.expect_exact("_python_argcomplete_ruyi")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["--output-completion-script=zsh"],
        env=isolated_env,
    )
    try:
        child.expect_exact("#compdef ruyi")
        child.expect_exact("_python_argcomplete_ruyi")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    child = spawn_ruyi(
        ruyi_exe,
        ["--output-completion-script=fish"],
        env=isolated_env,
    )
    try:
        child.expect_exact("ValueError: Unsupported shell: fish")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 1