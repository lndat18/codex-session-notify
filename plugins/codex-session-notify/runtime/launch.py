#!/usr/bin/env python3
"""Launch an isolated interactive CLI whose notify child identifies its terminal."""
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent


def command(arguments, binary=None):
    binary = binary or shutil.which('codex')
    if not binary:
        raise ValueError('Codex CLI is not on PATH.')
    # A remote server does not execute the notification hook in this terminal's
    # ancestry. Do not advertise exact routing for that launch mode.
    if any(arg == '--remote' or arg.startswith('--remote=') for arg in arguments):
        raise ValueError('Exact terminal notifications require a local CLI, not --remote.')
    for index, arg in enumerate(arguments):
        setting = None
        if arg in ('-c', '--config') and index + 1 < len(arguments):
            setting = arguments[index + 1]
        elif arg.startswith('--config='):
            setting = arg.split('=', 1)[1]
        elif arg.startswith('-c') and len(arg) > 2:
            setting = arg[2:]
        if setting and setting.split('=', 1)[0].strip() == 'notify':
            raise ValueError('This launcher owns the per-invocation notify hook; omit the notify override.')
    hook = [sys.executable, str(ROOT / 'notify.py')]
    # JSON arrays of quoted strings are valid TOML arrays. argv is passed directly
    # to exec, so spaces and shell metacharacters do not receive shell expansion.
    return [binary, '--no-daemon', '-c', 'notify=' + json.dumps(hook), *arguments]


def main():
    try:
        argv = command(sys.argv[1:])
        os.execv(argv[0], argv)
    except (OSError, ValueError) as error:
        print('codex-notify:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
