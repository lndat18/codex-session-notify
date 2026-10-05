$ErrorActionPreference = 'Stop'
$protocol = 'HKCU:\Software\Classes\codex-session'
$command = $protocol + '\shell\open\command'
if (Test-Path $command) {
    $registered = (Get-Item $command).GetValue('')
    if ($registered -match 'CodexSessionNotify\\CodexFocus\.exe') { Remove-Item $protocol -Recurse -Force }
}
$key = 'HKCU:\Software\Classes\AppUserModelId\CodexCLI.SessionNotify'
if (Test-Path $key) { Remove-Item $key -Recurse -Force }
$shortcut = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Codex Notifications.lnk'
if (Test-Path $shortcut) { Remove-Item $shortcut -Force }
