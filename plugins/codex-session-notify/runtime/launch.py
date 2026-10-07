#!/usr/bin/env python3
"""Launch an isolated interactive CLI whose notify child identifies its terminal."""
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent


def command(arguments, binary=None, automatic=False):
    binary = binary or shutil.which('codex')
    if not binary:
        raise ValueError('Codex CLI is not on PATH.')
    if automatic:
        # Only local interactive launches need terminal routing. Administration,
        # noninteractive jobs, remote clients and explicitly configured hooks pass
        # through to the genuine binary unchanged.
        admin = {'exec', 'e', 'review', 'login', 'logout', 'mcp', 'plugin',
                 'app-server', 'remote-control', 'completion', 'update', 'doctor',
                 'sandbox', 'debug', 'apply', 'a', 'queue', 'archive', 'delete',
                 'migrate-rollouts', 'unarchive', 'cloud', 'exec-server', 'features',
                 'help', 'agents'}
        value_options = {'-c', '--config', '-m', '--model', '-p', '--profile',
                         '-C', '--cd', '-s', '--sandbox', '-a', '--ask-for-approval',
                         '--add-dir', '-i', '--image', '--enable', '--disable',
                         '--remote', '--remote-auth-token-env'}
        skip = False
        for arg in arguments:
            if skip:
                skip = False
                continue
            if arg in value_options:
                skip = True
                continue
            if arg.startswith('-'):
                continue
            if arg in admin:
                return [binary, *arguments]
            break
        if any(a in ('--help', '-h', '--version', '-V', '--remote') or
               a.startswith('--remote=') for a in arguments):
            return [binary, *arguments]
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
            if automatic:
                return [binary, *arguments]
            raise ValueError('This launcher owns the per-invocation notify hook; omit the notify override.')
    hook = [sys.executable, str(ROOT / 'notify.py')]
    # JSON arrays of quoted strings are valid TOML arrays. argv is passed directly
    # to exec, so spaces and shell metacharacters do not receive shell expansion.
    return [binary, '--no-daemon', '-c', 'notify=' + json.dumps(hook), *arguments]


def main():
    try:
        arguments = sys.argv[1:]
        automatic = bool(arguments and arguments[0] == '--automatic')
        if automatic:
            arguments = arguments[1:]
        argv = command(arguments, binary=os.environ.get('CODEX_NOTIFY_BINARY'), automatic=automatic)
        os.execv(argv[0], argv)
    except (OSError, ValueError) as error:
        print('codex-notify:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
