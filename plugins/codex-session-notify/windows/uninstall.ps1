$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$data = [Console]::In.ReadToEnd() | ConvertFrom-Json
if ($data.id -notmatch '^[0-9a-f]{64}$') { throw 'Invalid installation identity' }
$root = Join-Path $env:LOCALAPPDATA 'CodexSessionNotify'
if (Test-Path (Join-Path $root 'installation.lock')) { throw 'Another installation transaction is in progress' }
$target = Join-Path $root ('installations\' + $data.id)
# Retain files/logs; only remove this distribution's active routing registration.
$config = Join-Path $target 'click-config.json'
if (Test-Path $config) { Move-Item $config ($config + '.removed-' + [Guid]::NewGuid().ToString()) }
$others = @(Get-ChildItem (Join-Path $root 'installations') -Filter 'click-config.json' -Recurse -ErrorAction SilentlyContinue)
if ($others.Count -gt 0 -or (Test-Path (Join-Path $root 'click-config.json'))) { exit 0 }
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
