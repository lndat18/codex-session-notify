param([switch]$ProbeOnly, [long]$WindowHandle = 0, [string]$TerminalName = '')
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
function Test-CodexTerminalVisible([long]$handle, [string]$name) {
    try {
        Add-Type -AssemblyName UIAutomationClient
        Add-Type -AssemblyName UIAutomationTypes
        $root = [Windows.Automation.AutomationElement]::FromHandle([IntPtr]$handle)
        if ($null -eq $root -or $root.Current.IsOffscreen) { return $false }
        $condition = [Windows.Automation.PropertyCondition]::new(
            [Windows.Automation.AutomationElement]::ClassNameProperty, 'xterm-helper-textarea')
        $elements = $root.FindAll([Windows.Automation.TreeScope]::Descendants, $condition)
        $pattern = '^Terminal [0-9]+,\s*' + [regex]::Escape($name) + '(?: Run the command:|$)'
        foreach ($element in $elements) {
            $rect = $element.Current.BoundingRectangle
            if (-not $element.Current.IsOffscreen -and $rect.Width -gt 0 -and $rect.Height -gt 0 -and
                $element.Current.Name -match $pattern) { return $true }
        }
    } catch { return $false }
    return $false
}
if ($ProbeOnly) {
    @{ visible = (Test-CodexTerminalVisible $WindowHandle $TerminalName) } | ConvertTo-Json -Compress
    exit 0
}
$data = [Console]::In.ReadToEnd() | ConvertFrom-Json
if ($data.watch_candidate) {
    Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class CodexForeground {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int count);
}
'@
    $hwnd = [CodexForeground]::GetForegroundWindow()
    $foregroundPid = [uint32]0
    [void][CodexForeground]::GetWindowThreadProcessId($hwnd, [ref]$foregroundPid)
    $process = Get-Process -Id $foregroundPid -ErrorAction SilentlyContinue
    if ($process.ProcessName -in @('Code', 'Code - Insiders')) {
        $caption = [Text.StringBuilder]::new(1024)
        [void][CodexForeground]::GetWindowText($hwnd, $caption, 1024)
        $sameWorkspace = $false
        foreach ($workspaceName in $data.workspace_names) {
            $suffix = [regex]::Escape(' - ' + $workspaceName) + '(?: \[WSL: [^\]]+\])? - Visual Studio Code(?: - Insiders)?$'
            if ($caption.ToString() -match $suffix) { $sameWorkspace = $true; break }
        }
        if ($sameWorkspace -and (Test-CodexTerminalVisible $hwnd.ToInt64() $data.terminal_name)) {
            @{ status = 'suppressed'; reason = 'matching terminal visible in focused VS Code window' } | ConvertTo-Json -Compress
            exit 0
        }
    }
}
$null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.UI.Notifications.ToastNotifier, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
function Esc([string]$value) { [Security.SecurityElement]::Escape($value) }
$icon = Join-Path $PSScriptRoot 'codex.png'
$uri = Esc ([Uri]$icon).AbsoluteUri
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$activation = ''
if ($data.launch_uri) {
    if ($data.launch_uri -notmatch '^codex-session://focus/([0-9a-f-]{36})$') { throw 'Invalid focus URI' }
    $token = $Matches[1]
    $focusExe = Join-Path $PSScriptRoot 'CodexFocus.exe'
    $targetName = [string]$data.target_workspace_name
    if (-not $targetName) { $targetName = [string]$data.project }
    $bound = Start-Process -FilePath $focusExe -ArgumentList @('--bind', $token, ('"' + $targetName + '"')) -WindowStyle Hidden -PassThru -Wait
    if ($bound.ExitCode -ne 0) { throw 'Could not bind the notification to the original VS Code window.' }
    $activation = " activationType='protocol' launch='$(Esc $data.launch_uri)'"
}
$xml.LoadXml("<toast$activation duration='short'><visual><binding template='ToastGeneric'><image placement='appLogoOverride' src='$uri'/><text hint-maxLines='1'>$(Esc $data.title)</text><text hint-maxLines='3'>$(Esc $data.body)</text><text placement='attribution'>$(Esc $data.project)</text></binding></visual><audio src='ms-winsoundevent:Notification.Default'/></toast>")
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$toast.Tag = ([string]$data.session_id).Replace('-', '').Substring(0, [Math]::Min(16, ([string]$data.session_id).Replace('-', '').Length))
$toast.Group = 'codex-complete'
$toast.ExpirationTime = [DateTimeOffset]::Now.AddMinutes(5)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('CodexCLI.SessionNotify')
if ($null -eq $notifier) { throw 'Windows could not create the Codex toast notifier.' }
$notifier.Show($toast)
Start-Sleep -Milliseconds 500
@{ status = 'sent'; app = 'Codex'; session = $data.session_id } | ConvertTo-Json -Compress
