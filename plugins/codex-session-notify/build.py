"""Build the offline VS Code extension and distributable ZIP using Python only."""
from pathlib import Path
import json
import zipfile
import hashlib

HERE = Path(__file__).resolve().parent


def vsix():
    manifest = json.loads((HERE / 'extension/package.json').read_text())
    name, version, publisher = (manifest[k] for k in ('name', 'version', 'publisher'))
    output = HERE / 'dist' / f'{name}-{version}.vsix'
    output.parent.mkdir(exist_ok=True)
    xml = f'''<?xml version="1.0" encoding="utf-8"?><PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"><Metadata><Identity Language="en-US" Id="{name}" Version="{version}" Publisher="{publisher}"/><DisplayName>Codex Session Notifications</DisplayName><Description xml:space="preserve">Return to the original Codex terminal from Windows notifications.</Description><Tags/><Categories>Other</Categories><GalleryFlags>Public</GalleryFlags><Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.96.2"/></Properties></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/><Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets></PackageManifest>'''
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('extension.vsixmanifest', xml)
        z.writestr('[Content_Types].xml', '''<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/><Default Extension="vsixmanifest" ContentType="text/xml"/></Types>''')
        for f in sorted((HERE / 'extension').iterdir()):
            z.write(f, 'extension/' + f.name)
    return output


if __name__ == '__main__':
    extension = vsix()
    bundle = HERE.parents[1]
    version = json.loads((HERE / 'plugin.json').read_text())['version']
    archive = bundle.parent / f'codex-session-notify-{version}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(bundle.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts and '.git' not in f.parts and f.suffix != '.pyc':
                z.write(f, f'codex-session-notify-{version}/' + str(f.relative_to(bundle)))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    print(extension)
    print(archive)
