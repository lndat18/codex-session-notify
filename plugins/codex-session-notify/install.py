#!/usr/bin/env python3
"""Install, inspect, or remove Codex terminal notifications on Windows + WSL."""
import argparse
import base64
import datetime
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

HERE = Path(__file__).resolve().parent
VERSION = '1.1.0'
EXTENSION = 'local-wsl.codex-existing-terminal-focus'
UNIT = 'codex-session-notify.service'
CODEX = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')).resolve()
ROOT = CODEX / 'session-notify'
CONFIG = CODEX / 'config.toml'
SERVICE = Path.home() / '.config/systemd/user' / UNIT
REMOVE = object()


def run(args, **kwargs):
    return subprocess.run(args, check=True, timeout=60, **kwargs)


def powershell():
    binary = shutil.which('powershell.exe') or '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
    if not Path(binary).exists():
        raise ValueError('Windows PowerShell interop is unavailable. Run inside WSL.')
    return binary


def ps_script(source, payload=None):
    encoded = base64.b64encode(source.encode('utf-16le')).decode()
    result = run([powershell(), '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-EncodedCommand', encoded],
                 input=json.dumps(payload) if payload is not None else '', text=True, capture_output=True)
    return result.stdout.strip()


def code_env():
    servers = Path.home() / '.vscode-server'
    binaries = list(servers.glob('bin/*/bin/remote-cli/code')) + list(servers.glob('cli/servers/*/server/bin/remote-cli/code'))
    binaries.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    fallback = shutil.which('code')
    if fallback:
        binaries.append(Path(fallback))
    candidates = [os.environ.copy()]
    sockets = sorted(Path(f'/run/user/{os.getuid()}').glob('vscode-ipc-*.sock'), key=lambda p: p.stat().st_mtime, reverse=True)
    candidates.extend({**os.environ, 'VSCODE_IPC_HOOK_CLI': str(sock)} for sock in sockets)
    for binary in binaries:
        for env in candidates:
            result = subprocess.run([str(binary), '--list-extensions'], env=env, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                return str(binary), env, set(result.stdout.splitlines())
    raise ValueError('No live VS Code WSL connection. Open a WSL folder in VS Code and retry.')


def setting(text, section, key, value):
    """Change exactly one supported single-line TOML setting, preserving other text."""
    parsed = tomllib.loads(text)
    table = parsed.get(section, {}) if section else parsed
    start, end = 0, len(text)
    if section:
        header = re.search(r'^\[' + re.escape(section) + r'\][ \t]*(?:#.*)?\n', text, re.M)
        if header:
            start = header.end()
            next_table = re.search(r'^\[', text[start:], re.M)
            end = start + next_table.start() if next_table else len(text)
        elif section in parsed:
            raise ValueError(f'Unsupported dotted or inline [{section}] configuration; no changes made.')
        elif value is REMOVE:
            return text
        else:
            text = text.rstrip() + f'\n\n[{section}]\n'
            start = end = len(text)
    else:
        header = re.search(r'^\[', text, re.M)
        end = header.start() if header else len(text)
    block = text[start:end]
    match = re.search(r'^' + re.escape(key) + r'\s*=.*(?:\n|$)', block, re.M)
    replacement = '' if value is REMOVE else f'{key} = {json.dumps(value, ensure_ascii=False)}\n'
    if key in table:
        if not match or tomllib.loads(match.group()).get(key) != table[key]:
            raise ValueError(f'Multiline or complex {section}.{key} needs manual editing; no changes made.')
        block = block[:match.start()] + replacement + block[match.end():]
    elif value is not REMOVE:
        block = replacement + block
    result = text[:start] + block + text[end:]
    tomllib.loads(result)
    return result


def config_plan(original, replace_notify=False):
    parsed = tomllib.loads(original)
    if parsed.get('notify') and not replace_notify:
        raise ValueError('An existing notify hook is configured. Use --replace-notify to replace it with a backup.')
    prior = parsed.get('tui', {}).get('notifications', True)
    notifications = prior if prior is False else (
        [event for event in prior if event != 'agent-turn-complete'] if isinstance(prior, list) else ['approval-requested'])
    updated = setting(setting(original, '', 'notify', []), 'tui', 'notifications', notifications)
    saved = {}
    for section, key in [('', 'notify'), ('tui', 'notifications')]:
        table = parsed.get(section, {}) if section else parsed
        saved[f'{section}.{key}'] = {'exists': key in table, 'value': table.get(key)}
    return updated, saved, {'notify': [], 'notifications': notifications}


def install(args):
    if not os.environ.get('WSL_DISTRO_NAME'):
        raise ValueError('This plugin requires Windows + WSL. Run inside a VS Code WSL terminal.')
    if CODEX != Path.home() / '.codex':
        raise ValueError('Version 1.0 supports the default ~/.codex directory; custom CODEX_HOME requires extension configuration.')
    original = CONFIG.read_text() if CONFIG.exists() else ''
    updated, saved, applied = config_plan(original, args.replace_notify)
    interpreter = shutil.which('python3') or sys.executable
    plan = {'version': VERSION, 'runtime': str(ROOT), 'service': str(SERVICE), 'extension': EXTENSION,
            'distro': os.environ['WSL_DISTRO_NAME'], 'user': getpass.getuser(),
            'changes': ['backup installation', 'install VS Code extension', 'compile hidden Windows activation helper',
                        'register click protocol and toast sender', 'update notification settings only', 'restart user service']}
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    ps = powershell()
    code, env, extensions = code_env()
    run(['systemctl', '--user', 'show-environment'], capture_output=True)
    extension_file = HERE / 'dist/codex-existing-terminal-focus-1.1.0.vsix'
    if not extension_file.exists():
        from build import vsix
        extension_file = vsix()
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = CODEX / 'session-notify-backups' / stamp
    backup.mkdir(parents=True, exist_ok=True)
    if ROOT.exists():
        shutil.copytree(ROOT, backup / 'runtime')
    if CONFIG.exists():
        shutil.copy2(CONFIG, backup / 'config.toml')
    if SERVICE.exists():
        shutil.copy2(SERVICE, backup / UNIT)
    previous_state = json.loads((ROOT / 'install-state.json').read_text()) if (ROOT / 'install-state.json').exists() else {}
    print('Backup:', backup, flush=True)
    run(['systemctl', '--user', 'stop', UNIT], capture_output=True) if SERVICE.exists() else None
    try:
        ROOT.mkdir(parents=True, exist_ok=True)
        for name in ('notify.py', 'watcher.py', 'click.py'):
            shutil.copy2(HERE / 'runtime' / name, ROOT / name)
        payload = {'files': {name: base64.b64encode((HERE / 'windows' / name).read_bytes()).decode()
                             for name in ('codex.png', 'toast.ps1', 'Focus.cs')},
                   'config': {'distro': os.environ['WSL_DISTRO_NAME'], 'user': getpass.getuser(),
                              'bridge': str(ROOT / 'click.py'),
                              'bridgeArguments': subprocess.list2cmdline(['-d', os.environ['WSL_DISTRO_NAME'], '-u', getpass.getuser(),
                                                                          '--exec', '/usr/bin/python3', str(ROOT / 'click.py')])}}
        windows = json.loads(ps_script((HERE / 'windows/setup.ps1').read_text(), payload).splitlines()[-1])
        windows['powershell'] = ps
        (ROOT / 'windows.json').write_text(json.dumps(windows))
        run([code, '--install-extension', str(extension_file), '--force'], env=env)
        CONFIG.write_text(updated)
        SERVICE.parent.mkdir(parents=True, exist_ok=True)
        quote = lambda value: json.dumps(str(value).replace('%', '%%'))
        SERVICE.write_text('[Unit]\nDescription=Codex completion notifications and existing terminal focus\n\n'
                           '[Service]\nType=simple\nExecStart=' + quote(interpreter) + ' ' + quote(ROOT / 'watcher.py') +
                           '\nWorkingDirectory=' + str(ROOT).replace('%', '%%') + '\nRestart=on-failure\nRestartSec=2\n\n[Install]\nWantedBy=default.target\n')
        (ROOT / 'install-state.json').write_text(json.dumps({'version': VERSION, 'installedAt': stamp, 'backup': str(backup),
                                                           'original': previous_state.get('original', saved), 'applied': applied,
                                                           'windows': windows}, indent=2))
        run(['systemctl', '--user', 'daemon-reload'])
        run(['systemctl', '--user', 'enable', '--now', UNIT])
    except Exception:
        # Restore the Linux installation; Windows copies and registry remain in Windows backups.
        if (backup / 'runtime').exists():
            failed = backup / 'failed-runtime'
            ROOT.rename(failed)
            shutil.copytree(backup / 'runtime', ROOT)
        if (backup / 'config.toml').exists():
            shutil.copy2(backup / 'config.toml', CONFIG)
        if (backup / UNIT).exists():
            shutil.copy2(backup / UNIT, SERVICE)
            subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True)
            subprocess.run(['systemctl', '--user', 'start', UNIT], capture_output=True)
        raise
    print('Installed Codex Session Notifications', VERSION)
    print('If no terminal window records appear, run Developer: Reload Window once in each VS Code WSL window.')


def status(_args):
    service = subprocess.run(['systemctl', '--user', 'is-active', UNIT], capture_output=True, text=True)
    windows = json.loads((ROOT / 'windows.json').read_text()) if (ROOT / 'windows.json').exists() else {}
    state = json.loads((ROOT / 'install-state.json').read_text()) if (ROOT / 'install-state.json').exists() else {}
    active = []
    import time
    for path in (ROOT / 'terminal-windows').glob('*.json'):
        try:
            row = json.loads(path.read_text())
            if 0 <= time.time() - row.get('timestamp', 0) < 5:
                active.append({'workspace': row.get('workspace'), 'terminals': len(row.get('terminals', []))})
        except (ValueError, OSError):
            continue
    print(json.dumps({'version': state.get('version', 'legacy' if ROOT.exists() else None),
                      'service': service.stdout.strip(), 'runtime': str(ROOT), 'windows': windows, 'activeWindows': active}, indent=2))


def uninstall(args):
    state_file = ROOT / 'install-state.json'
    if not state_file.exists():
        raise ValueError('No packaged installation found. Legacy installation is left intact.')
    state = json.loads(state_file.read_text())
    if args.dry_run:
        print(json.dumps({'remove': [UNIT, EXTENSION, 'codex-session protocol', 'Codex toast registration'],
                          'restore': 'Only notification settings that still match installed values',
                          'keep': ['logs', 'backups', 'other Codex settings']}, indent=2))
        return
    original = CONFIG.read_text()
    parsed = tomllib.loads(original)
    updated = original
    for section, key, expected in [('', 'notify', state['applied']['notify']), ('tui', 'notifications', state['applied']['notifications'])]:
        table = parsed.get(section, {}) if section else parsed
        if table.get(key) == expected:
            before = state['original'][f'{section}.{key}']
            updated = setting(updated, section, key, before['value'] if before['exists'] else REMOVE)
    code, env, _ = code_env()
    run(['systemctl', '--user', 'disable', '--now', UNIT])
    run([code, '--uninstall-extension', EXTENSION], env=env)
    ps_script((HERE / 'windows/uninstall.ps1').read_text())
    CONFIG.write_text(updated)
    SERVICE.unlink(missing_ok=True)
    run(['systemctl', '--user', 'daemon-reload'])
    state_file.rename(ROOT / ('install-state.removed-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.json'))
    print('Removed the notification service and click handler. Logs and backups retained:', ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('install', help='Install or update the reusable notification runtime')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--replace-notify', action='store_true', help='Replace an existing notification hook, with backup')
    p.set_defaults(action=install)
    p = sub.add_parser('status', help='Report the service and existing terminal windows')
    p.set_defaults(action=status)
    p = sub.add_parser('uninstall', help='Stop notifications and remove owned registrations')
    p.add_argument('--dry-run', action='store_true')
    p.set_defaults(action=uninstall)
    args = parser.parse_args()
    try:
        args.action(args)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('Error:', error, file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
