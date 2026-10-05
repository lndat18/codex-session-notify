param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$title = 'Codex Session Notifications'
function Ask($message) {
    return [System.Windows.Forms.MessageBox]::Show($message, $title, 'YesNo', 'Question') -eq 'Yes'
}
function WslRun([string[]]$Arguments) {
    $result = & wsl.exe @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($result -join "`n") }
    return ($result -join "`n").Trim()
}
try {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { throw 'Install Windows Subsystem for Linux first: https://learn.microsoft.com/windows/wsl/install' }
    $distros = @((& wsl.exe --list --quiet) | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ -and $_ -notlike 'docker-desktop*' })
    if ($distros.Count -eq 0) { throw 'No WSL Linux distribution found. Install Ubuntu using the Microsoft Store, then open it once.' }
    if ($CheckOnly) { $distros; exit 0 }
    if (-not (Ask "Install notifications for all your Codex sessions in VS Code + WSL?`n`nCai thong bao cho tat ca session Codex trong VS Code + WSL?")) { exit 0 }
    $distro = $distros[0]
    if ($distros.Count -gt 1) {
        $form = New-Object System.Windows.Forms.Form
        $form.Text = 'Choose WSL / Chon WSL'; $form.Width = 380; $form.Height = 150; $form.StartPosition = 'CenterScreen'
        $select = New-Object System.Windows.Forms.ComboBox
        $select.Left = 20; $select.Top = 15; $select.Width = 320; $select.DropDownStyle = 'DropDownList'
        $select.Items.AddRange([object[]]$distros); $select.SelectedIndex = 0
        $button = New-Object System.Windows.Forms.Button
        $button.Text = 'Install / Cai dat'; $button.Left = 210; $button.Top = 55; $button.Width = 130; $button.DialogResult = 'OK'
        $form.Controls.AddRange(@($select, $button)); $form.AcceptButton = $button
        if ($form.ShowDialog() -ne 'OK') { exit 0 }
        $distro = [string]$select.SelectedItem
    }
    WslRun -Arguments @('-d', $distro, '--exec', 'python3', '-c', 'import sys; assert sys.version_info >= (3,11), "Python 3.11 or newer is required."') | Out-Null
    $source = WslRun -Arguments @('-d', $distro, '--exec', 'wslpath', '-u', $PSScriptRoot)
    $homePath = WslRun -Arguments @('-d', $distro, '--exec', 'printenv', 'HOME')
    $codePaths = @("$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe", "$env:ProgramFiles\Microsoft VS Code\Code.exe")
    $code = $codePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $code) { throw 'Install Visual Studio Code first: https://code.visualstudio.com/' }
    $codeCli = Join-Path (Split-Path $code) 'bin\code.cmd'
    & $codeCli --install-extension ms-vscode-remote.remote-wsl | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the VS Code WSL extension.' }
    & $code --folder-uri "vscode-remote://wsl+$distro$homePath" | Out-Null
    $replace = @()
    $hook = WslRun -Arguments @('-d', $distro, '--exec', 'python3', "$source/bootstrap.py", '--check-hook')
    if ($hook -eq 'yes') {
        if (-not (Ask "An existing notification hook was found. Back it up and replace it?`n`nDa co cau hinh thong bao. Sao luu va thay the?")) { exit 0 }
        $replace = @('--replace-notify')
    }
    Write-Host 'Installing. Please keep this window open / Dang cai dat...'
    & wsl.exe -d $distro --exec python3 "$source/bootstrap.py" @replace
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed. See the details in this window. Requirements: Python 3.11+, Codex CLI, and WSL with systemd enabled.' }
    [System.Windows.Forms.MessageBox]::Show("Installed! Notifications now cover your Codex sessions in this WSL distribution.`nIf an already open VS Code window does not respond, reload that window once.`n`nDa cai xong! Ap dung cho cac session Codex trong WSL da chon.", $title, 'OK', 'Information') | Out-Null
} catch {
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, $title, 'OK', 'Error') | Out-Null
    Write-Host $_.Exception.Message
    Read-Host 'Press Enter to close / Nhan Enter de dong'
    exit 1
}
