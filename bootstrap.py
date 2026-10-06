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


def find_codex():
    binary = shutil.which('codex')
    if binary:
        return binary
    candidates = sorted((Path.home() / '.nvm/versions/node').glob('*/bin/codex'),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    return str(candidates[0]) if candidates else None


def check_environment():
    """Read prerequisites before asking to install or changing machine state."""
    if not os.environ.get('WSL_DISTRO_NAME'):
        raise ValueError('Open a WSL terminal / Mở terminal WSL để cài.')
    configured_home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')).resolve()
    if configured_home != (Path.home() / '.codex').resolve():
        raise ValueError('This installer requires the default ~/.codex / Bộ cài cần thư mục ~/.codex mặc định.')
    source = Path(__file__).resolve().parent
    sys.path.insert(0, str(source / 'plugins/codex-session-notify'))
    from install import powershell, ps_script
    powershell()
    if not shutil.which('systemctl'):
        raise ValueError('systemd is unavailable / Cần systemd trong WSL để chạy dịch vụ thông báo.')
    systemd = subprocess.run(['systemctl', '--user', 'show-environment'],
                             capture_output=True, text=True, timeout=15)
    if systemd.returncode:
        raise ValueError('WSL systemd user session is unavailable / Cần bật systemd trong WSL và khởi động lại WSL.')
    if not find_codex():
        raise ValueError('Codex CLI was not found / Cần cài Codex CLI trước.')
    ps_script(r'''
$ErrorActionPreference = 'Stop'
$paths = @("$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe", "$env:ProgramFiles\Microsoft VS Code\Code.exe")
$code = $paths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $code) { throw 'Install VS Code first / Cần cài VS Code trước.' }
if (-not (Test-Path (Join-Path (Split-Path $code) 'bin\code.cmd'))) { throw 'VS Code command line support is missing / Cần sửa hoặc cài lại VS Code.' }
''')


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
        print('Checking environment / Đang kiểm tra môi trường...', flush=True)
        check_environment()
        print('Environment ready / Môi trường đã sẵn sàng.')
        print('Installs notifications and click back to your Codex session. Required components and VS Code WSL support are set up automatically.')
        print('Cài thông báo và bấm về session Codex. Bộ cài tự thiết lập các thành phần cần thiết, có thể mở VS Code WSL.')
        install_runtime = ask('Install Codex notifications / Cài thông báo Codex?')
        if install_runtime and existing_hook and not args.replace_notify:
            args.replace_notify = ask('Back up and replace the existing notification hook / Sao lưu và thay hook thông báo cũ?')
            if not args.replace_notify:
                install_runtime = False
                print('Notifications skipped / Bỏ qua cài thông báo.')
    else:
        install_runtime = True
    # The optional skill is offered after the notification installation.
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
                print('Preparing VS Code WSL / Đang chuẩn bị VS Code WSL...', flush=True)
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
        print('Notifications installed / Đã cài thông báo.')
    if args.interactive:
        print('The optional skill lets Codex inspect, update and uninstall notifications.')
        print('Skill tuỳ chọn giúp Codex kiểm tra, cập nhật và gỡ bộ thông báo.')
        if not ask('Add the Codex management skill / Thêm skill quản lý vào Codex?'):
            print('Done / Hoàn tất.')
            return
    retain_source()
    codex = find_codex()
    if not codex:
        print('Skill skipped: Codex CLI is unavailable / Bỏ qua skill: chưa tìm thấy Codex CLI.')
        return
    env = {**os.environ, 'PATH': str(Path(codex).parent) + os.pathsep + os.environ.get('PATH', '')}
    for arguments in (['plugin', 'marketplace', 'add', str(destination)],
                      ['plugin', 'add', 'codex-session-notify@local-notifications']):
        result = subprocess.run([codex, *arguments], env=env, timeout=60)
        if result.returncode:
            raise SystemExit('Skill registration failed; installed notifications are retained / Đăng ký skill thất bại; thông báo đã cài vẫn được giữ.')
    print('Skill installed. Done / Đã thêm skill. Hoàn tất.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('Installation error / Lỗi cài đặt:', error, file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        raise SystemExit(1)
