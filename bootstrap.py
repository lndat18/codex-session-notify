"""Interactive terminal installer and Windows wizard bridge."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

if sys.version_info < (3, 11):
    raise SystemExit('Python 3.11+ is required / Cần Python 3.11 trở lên.')
import tomllib


def ask(message):
    while True:
        try:
            answer = input(message + ' [yes/no]: ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit('\nCancelled / Đã huỷ.')
        if answer in ('yes', 'y', 'có', 'co'):
            return True
        if answer in ('no', 'n', 'không', 'khong'):
            return False
        print('Enter yes or no / Nhập yes hoặc no.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-hook', action='store_true')
    parser.add_argument('--replace-notify', action='store_true')
    parser.add_argument('--interactive', action='store_true')
    args = parser.parse_args()
    config = Path.home() / '.codex/config.toml'
    existing_hook = bool(config.exists() and tomllib.loads(config.read_text()).get('notify'))
    if args.check_hook:
        print('yes' if existing_hook else 'no')
        return
    if not os.environ.get('WSL_DISTRO_NAME'):
        raise SystemExit('Run this installer in WSL / Mở terminal WSL để cài.')
    if args.interactive:
        print('Codex Session Notifications — cài đặt từng phần')
        print('A: Desktop notifications + click back to session. Includes the required VS Code extension, Windows helper and background service.')
        print('A: Thông báo và bấm về session. Gồm extension VS Code, bộ xử lý Windows và dịch vụ nền cần thiết.')
        install_runtime = ask('Install A / Cài phần A?')
        if install_runtime and existing_hook and not args.replace_notify:
            args.replace_notify = ask('Back up and replace the existing notification hook / Sao lưu và thay hook thông báo cũ?')
            if not args.replace_notify:
                install_runtime = False
                print('Skipped A / Bỏ qua phần A.')
    else:
        install_runtime = True
    # A and B are offered in sequence; B can be installed even if A is skipped.
    source = Path(__file__).resolve().parent
    destination = Path.home() / '.local/share/codex-session-notify'

    def retain_source():
        if source != destination:
            shutil.copytree(source, destination, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        return destination / 'plugins/codex-session-notify'

    if install_runtime:
        installer = retain_source()
        sys.path.insert(0, str(installer))
        from install import code_env, ps_script
        try:
            code_env()
        except (ValueError, OSError, subprocess.SubprocessError):
            if args.interactive:
                if not ask('Open VS Code WSL and install its WSL support / Mở VS Code WSL và cài hỗ trợ WSL?'):
                    raise SystemExit('A needs a live VS Code WSL connection / Phần A cần kết nối VS Code WSL.')
                ps_script(r'''
$ErrorActionPreference = 'Stop'
$data = [Console]::In.ReadToEnd() | ConvertFrom-Json
$paths = @("$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe", "$env:ProgramFiles\Microsoft VS Code\Code.exe")
$code = $paths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $code) { throw 'Install VS Code first / Cần cài VS Code trước.' }
$cli = Join-Path (Split-Path $code) 'bin\code.cmd'
& $cli --install-extension ms-vscode-remote.remote-wsl | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not install WSL support' }
& $code --folder-uri ('vscode-remote://wsl+' + $data.distro + $data.home) | Out-Null
''', {'distro': os.environ['WSL_DISTRO_NAME'], 'home': str(Path.home())})
            for attempt in range(45):
                try:
                    code_env()
                    break
                except (ValueError, OSError, subprocess.SubprocessError):
                    if attempt == 44:
                        raise SystemExit('VS Code WSL is not ready. Open a WSL folder in VS Code and run install.sh again.')
                    time.sleep(2)
        command = [sys.executable, str(installer / 'install.py'), 'install']
        if args.replace_notify:
            command.append('--replace-notify')
        subprocess.run(command, check=True)
        print('A installed / Đã cài phần A.')
    if args.interactive:
        print('B: Optional Codex maintenance skill / Skill Codex để kiểm tra, cập nhật và gỡ cài đặt (tuỳ chọn).')
        if not ask('Install B / Cài phần B?'):
            print('Done / Hoàn tất.')
            return
    retain_source()
    codex = shutil.which('codex')
    if not codex:
        candidates = sorted((Path.home() / '.nvm/versions/node').glob('*/bin/codex'), key=lambda p: p.stat().st_mtime, reverse=True)
        codex = str(candidates[0]) if candidates else None
    if not codex:
        print('Skipped B: Codex CLI is unavailable / Bỏ qua B: chưa tìm thấy Codex CLI.')
        return
    env = {**os.environ, 'PATH': str(Path(codex).parent) + os.pathsep + os.environ.get('PATH', '')}
    for arguments in (['plugin', 'marketplace', 'add', str(destination)],
                      ['plugin', 'add', 'codex-session-notify@local-notifications']):
        result = subprocess.run([codex, *arguments], env=env, timeout=60)
        if result.returncode:
            raise SystemExit('B registration failed; any completed A installation is retained / Đăng ký B thất bại; phần A đã cài vẫn được giữ.')
    print('B installed. Done / Đã cài phần B. Hoàn tất.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('Installation error / Lỗi cài đặt:', error, file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        raise SystemExit(1)
