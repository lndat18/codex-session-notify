$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
$dir = Join-Path $env:LOCALAPPDATA 'CodexSessionNotify'
$null = New-Item -ItemType Directory -Force -Path $dir
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-ffff'
if (Test-Path (Join-Path $dir 'CodexFocus.exe')) {
    $backup = Join-Path $dir ('backups\' + $stamp)
    $null = New-Item -ItemType Directory -Force -Path $backup
    foreach ($name in @('CodexFocus.exe','Focus.cs','toast.ps1','click-config.json','codex.png','codex.ico')) {
        $original = Join-Path $dir $name
        if (Test-Path $original) { Copy-Item $original (Join-Path $backup $name) }
    }
}
foreach ($item in $payload.files.PSObject.Properties) {
    [IO.File]::WriteAllBytes((Join-Path $dir $item.Name), [Convert]::FromBase64String($item.Value))
}
$stage = Join-Path $dir 'CodexFocus.staged.exe'
if (Test-Path $stage) { Remove-Item $stage }
Add-Type -Path (Join-Path $dir 'Focus.cs') -ReferencedAssemblies 'System.dll','System.Core.dll','System.Web.Extensions.dll' -OutputAssembly $stage -OutputType WindowsApplication
Move-Item $stage (Join-Path $dir 'CodexFocus.exe') -Force
[IO.File]::WriteAllText((Join-Path $dir 'click-config.json'), ($payload.config | ConvertTo-Json -Compress), [Text.UTF8Encoding]::new($false))
$protocol = 'HKCU:\Software\Classes\codex-session'
$null = New-Item $protocol -Force
Set-Item $protocol 'URL:Codex session notification'
$null = New-ItemProperty $protocol -Name 'URL Protocol' -Value '' -PropertyType String -Force
$command = $protocol + '\shell\open\command'
$null = New-Item $command -Force
$focusExe = Join-Path $dir 'CodexFocus.exe'
Set-Item $command ('"' + $focusExe + '" "%1"')
Add-Type -AssemblyName System.Drawing
$bitmap = [Drawing.Bitmap]::new((Join-Path $dir 'codex.png'))
$small = [Drawing.Bitmap]::new($bitmap, [Drawing.Size]::new(64,64))
$hicon = $small.GetHicon()
$icon = [Drawing.Icon]::FromHandle($hicon)
$icoPath = Join-Path $dir 'codex.ico'
$stream = [IO.File]::Create($icoPath)
try { $icon.Save($stream) } finally { $stream.Dispose(); $small.Dispose(); $bitmap.Dispose() }

$appId = 'CodexCLI.SessionNotify'
$key = "HKCU:\Software\Classes\AppUserModelId\$appId"
$null = New-Item -Path $key -Force
$null = New-ItemProperty -Path $key -Name DisplayName -Value 'Codex' -PropertyType String -Force
$null = New-ItemProperty -Path $key -Name IconUri -Value $icoPath -PropertyType ExpandString -Force
$null = New-ItemProperty -Path $key -Name ShowInSettings -Value 1 -PropertyType DWord -Force

# Install a Start Menu shortcut carrying the same AppUserModelID.
$shortcutPath = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Codex Notifications.lnk'
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($shortcutPath)
$link.TargetPath = $focusExe
$link.Arguments = ''
$link.Description = 'Codex CLI completion notifications from WSL'
$link.IconLocation = "$icoPath,0"
$link.Save()
Add-Type @'
using System;
using System.Runtime.InteropServices;
[StructLayout(LayoutKind.Sequential)] public struct NotifyPropertyKey {
    public Guid fmtid; public uint pid;
}
[StructLayout(LayoutKind.Explicit, Size=24)] public struct NotifyPropVariant {
    [FieldOffset(0)] public ushort vt;
    [FieldOffset(8)] public IntPtr value;
}
[ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface NotifyPropertyStore {
    [PreserveSig] int GetCount(out uint count);
    [PreserveSig] int GetAt(uint index, out NotifyPropertyKey key);
    [PreserveSig] int GetValue(ref NotifyPropertyKey key, out NotifyPropVariant value);
    [PreserveSig] int SetValue(ref NotifyPropertyKey key, ref NotifyPropVariant value);
    [PreserveSig] int Commit();
}
public static class NotifyShortcut {
    [DllImport("shell32.dll", CharSet=CharSet.Unicode, PreserveSig=true)]
    static extern int SHGetPropertyStoreFromParsingName(string path, IntPtr bind, uint flags,
        ref Guid iid, out NotifyPropertyStore store);
    public static void SetAppId(string path, string id) {
        Guid iid = typeof(NotifyPropertyStore).GUID;
        NotifyPropertyStore store;
        Marshal.ThrowExceptionForHR(SHGetPropertyStoreFromParsingName(path, IntPtr.Zero, 2, ref iid, out store));
        var key = new NotifyPropertyKey { fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"), pid = 5 };
        var value = new NotifyPropVariant { vt = 31, value = Marshal.StringToCoTaskMemUni(id) };
        try {
            Marshal.ThrowExceptionForHR(store.SetValue(ref key, ref value));
            Marshal.ThrowExceptionForHR(store.Commit());
        } finally {
            Marshal.FreeCoTaskMem(value.value);
            Marshal.ReleaseComObject(store);
        }
    }
}
'@
[NotifyShortcut]::SetAppId($shortcutPath, $appId)
@{ script = (Join-Path $dir 'toast.ps1'); icon = $icoPath; directory = $dir; executable = $focusExe } | ConvertTo-Json -Compress
