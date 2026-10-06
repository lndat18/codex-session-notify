"""Build the offline VS Code extension and distributable ZIP using Python only."""
from pathlib import Path
import json
import zipfile
import hashlib

HERE = Path(__file__).resolve().parent

# Exact public artifacts: unrelated files are never swept into a release.
PUBLIC_FILES = (
    'README.md', 'Install.cmd', 'Install.ps1', 'bootstrap.py',
    '.agents/plugins/marketplace.json',
    'plugins/codex-session-notify/README.md',
    'plugins/codex-session-notify/plugin.json',
    'plugins/codex-session-notify/.codex-plugin/plugin.json',
    'plugins/codex-session-notify/install.py',
    'plugins/codex-session-notify/build.py',
    'plugins/codex-session-notify/skills/session-notify/SKILL.md',
    'plugins/codex-session-notify/extension/package.json',
    'plugins/codex-session-notify/extension/extension.js',
    'plugins/codex-session-notify/runtime/notify.py',
    'plugins/codex-session-notify/runtime/watcher.py',
    'plugins/codex-session-notify/runtime/click.py',
    'plugins/codex-session-notify/windows/Focus.cs',
    'plugins/codex-session-notify/windows/setup.ps1',
    'plugins/codex-session-notify/windows/transaction.ps1',
    'plugins/codex-session-notify/windows/uninstall.ps1',
    'plugins/codex-session-notify/windows/toast.ps1',
    'plugins/codex-session-notify/windows/codex.png',
)


def public_file(root, relative):
    file = root / relative
    if file.is_symlink() or root.resolve() not in file.resolve().parents or not file.is_file():
        raise ValueError('Missing or unsafe public artifact: ' + relative)
    # Reject a symlink in any ancestor as well as the final file.
    for parent in file.relative_to(root).parents:
        if (root / parent).is_symlink():
            raise ValueError('Symlinked public artifact directory: ' + relative)
    return file


def vsix():
    manifest = json.loads((HERE / 'extension/package.json').read_text())
    name, version, publisher = (manifest[k] for k in ('name', 'version', 'publisher'))
    output = HERE / 'dist' / f'{name}-{version}.vsix'
    output.parent.mkdir(exist_ok=True)
    xml = f'''<?xml version="1.0" encoding="utf-8"?><PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"><Metadata><Identity Language="en-US" Id="{name}" Version="{version}" Publisher="{publisher}"/><DisplayName>Codex Session Notifications</DisplayName><Description xml:space="preserve">Return to the original Codex terminal from Windows notifications.</Description><Tags/><Categories>Other</Categories><GalleryFlags>Public</GalleryFlags><Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.96.2"/></Properties></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/><Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets></PackageManifest>'''
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('extension.vsixmanifest', xml)
        z.writestr('[Content_Types].xml', '''<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/><Default Extension="vsixmanifest" ContentType="text/xml"/></Types>''')
        for name in ('package.json', 'extension.js'):
            f = public_file(HERE, 'extension/' + name)
            z.write(f, 'extension/' + name)
    return output


if __name__ == '__main__':
    extension = vsix()
    bundle = HERE.parents[1]
    version = json.loads((HERE / 'plugin.json').read_text())['version']
    archive = bundle.parent / f'codex-session-notify-{version}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        files = (*PUBLIC_FILES, str(extension.relative_to(bundle)))
        for relative in files:
            f = public_file(bundle, relative)
            z.write(f, f'codex-session-notify-{version}/' + relative)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    print(extension)
    print(archive)
