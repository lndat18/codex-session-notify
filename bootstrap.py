"""Windows wizard bridge: keep a durable source copy and install without shell commands."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import time
import tomllib

parser = argparse.ArgumentParser()
parser.add_argument('--check-hook', action='store_true')
parser.add_argument('--replace-notify', action='store_true')
args = parser.parse_args()
if args.check_hook:
    config = Path.home() / '.codex/config.toml'
    print('yes' if config.exists() and tomllib.loads(config.read_text()).get('notify') else 'no')
    raise SystemExit(0)
source = Path(__file__).resolve().parent
destination = Path.home() / '.local/share/codex-session-notify'
if source != destination:
    shutil.copytree(source, destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
installer = destination / 'plugins/codex-session-notify'
import sys
sys.path.insert(0, str(installer))
from install import code_env
for attempt in range(45):
    try:
        code_env()
        break
    except (ValueError, OSError, subprocess.SubprocessError):
        if attempt == 44:
            raise SystemExit('VS Code WSL did not become ready. Open the WSL folder in VS Code and run Install.cmd again.')
        time.sleep(2)
command = [sys.executable, str(installer / 'install.py'), 'install']
if args.replace_notify:
    command.append('--replace-notify')
subprocess.run(command, check=True)
# The runtime works independently of Codex plugin registration.
codex = shutil.which('codex')
if not codex:
    candidates = sorted((Path.home() / '.nvm/versions/node').glob('*/bin/codex'), key=lambda p: p.stat().st_mtime, reverse=True)
    codex = str(candidates[0]) if candidates else None
if codex:
    env = {**os.environ, 'PATH': str(Path(codex).parent) + os.pathsep + os.environ.get('PATH', '')}
    for arguments in (['plugin', 'marketplace', 'add', str(destination)],
                      ['plugin', 'add', 'codex-session-notify@local-notifications']):
        result = subprocess.run([codex, *arguments], env=env, timeout=60)
        if result.returncode:
            print('Notifications installed; optional Codex plugin registration was unavailable.')
            break
