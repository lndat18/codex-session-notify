$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$data = [Console]::In.ReadToEnd() | ConvertFrom-Json
if ($data.id -notmatch '^[0-9a-f]{64}$' -or $data.transaction -notmatch '^[0-9a-f-]{36}$') { throw 'Invalid transaction identity' }
$root = Join-Path $env:LOCALAPPDATA 'CodexSessionNotify'
$lock = Join-Path $root 'installation.lock'
$backup = Join-Path $root ('backups\transaction-' + $data.transaction)
$target = Join-Path $root ('installations\' + $data.id)
$shortcut = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Codex Notifications.lnk'
$keys = @('HKCU\Software\Classes\codex-session', 'HKCU\Software\Classes\AppUserModelId\CodexCLI.SessionNotify')
$files = @('CodexFocus.exe', 'codex.png', 'codex.ico')
if ($data.action -eq 'prepare') {
    $null = New-Item -ItemType Directory -Force $root
    # CreateNew refuses overlapping installs across WSL distributions.
    $stream = [IO.File]::Open($lock, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $bytes = [Text.Encoding]::UTF8.GetBytes($data.transaction); $stream.Write($bytes,0,$bytes.Length) } finally { $stream.Dispose() }
    try {
        $null = New-Item -ItemType Directory $backup
        foreach ($name in $files) { if (Test-Path (Join-Path $root $name)) { Copy-Item (Join-Path $root $name) (Join-Path $backup $name) } }
        if (Test-Path $target) { Copy-Item $target (Join-Path $backup 'installation') -Recurse }
        if (Test-Path $shortcut) { Copy-Item $shortcut (Join-Path $backup 'shortcut.lnk') }
        for ($i=0; $i -lt $keys.Count; $i++) {
            if (Test-Path ($keys[$i] -replace '^HKCU\\','HKCU:\')) {
                & "$env:WINDIR\System32\reg.exe" export $keys[$i] (Join-Path $backup "$i.reg") /y | Out-Null
                if ($LASTEXITCODE -ne 0) { throw 'Could not back up registry registration' }
            }
        }
        [IO.File]::WriteAllText((Join-Path $backup 'ready'), 'ready')
    } catch { Remove-Item $lock -Force; throw }
} else {
    if (-not (Test-Path $lock) -or [IO.File]::ReadAllText($lock) -ne $data.transaction) { throw 'Transaction lock does not belong to this installer' }
    if (-not (Test-Path (Join-Path $backup 'ready'))) { throw 'Transaction backup incomplete' }
    if ($data.action -eq 'rollback') {
        foreach ($name in $files) {
            $dest = Join-Path $root $name; $saved = Join-Path $backup $name
            if (Test-Path $saved) { Copy-Item $saved $dest -Force } elseif (Test-Path $dest) { Remove-Item $dest -Force }
        }
        if (Test-Path $target) { Remove-Item $target -Recurse -Force }
        if (Test-Path (Join-Path $backup 'installation')) { Copy-Item (Join-Path $backup 'installation') $target -Recurse }
        if (Test-Path (Join-Path $backup 'shortcut.lnk')) { Copy-Item (Join-Path $backup 'shortcut.lnk') $shortcut -Force } elseif (Test-Path $shortcut) { Remove-Item $shortcut -Force }
        for ($i=0; $i -lt $keys.Count; $i++) {
            $psKey = $keys[$i] -replace '^HKCU\\','HKCU:\'
            if (Test-Path $psKey) { Remove-Item $psKey -Recurse -Force }
            if (Test-Path (Join-Path $backup "$i.reg")) {
                & "$env:WINDIR\System32\reg.exe" import (Join-Path $backup "$i.reg") | Out-Null
                if ($LASTEXITCODE -ne 0) { throw 'Registry rollback failed; backup and lock retained' }
            }
        }
    } elseif ($data.action -ne 'commit') { throw 'Unknown transaction action' }
    Remove-Item $lock -Force
}
@{backup=$backup; action=$data.action} | ConvertTo-Json -Compress
