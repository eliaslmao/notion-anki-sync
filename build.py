"""Build current source and archive each release. Run: python build.py"""
import json
import pathlib
import py_compile
import zipfile
import shutil

root = pathlib.Path(__file__).resolve().parent
source = root / 'Quellcode'
if not source.is_dir(): source = root / 'notion_safe_sync'
version = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))['human_version']
release = root / 'Versionen' / version
release.mkdir(parents=True, exist_ok=True)
for path in source.glob('*.py'):
    py_compile.compile(str(path), doraise=True)
for destination in (root / 'Notion_Safe_Sync.ankiaddon', release / 'Notion_Safe_Sync.ankiaddon'):
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.iterdir()):
            if path.is_file() and not path.name.startswith('test_'):
                if path.name=='config.json':
                    archive.writestr(path.name,json.dumps({'NOTION_TOKEN':'','PAGES':[]}))
                else:
                    archive.write(path, path.name)
with zipfile.ZipFile(release / 'Notion_Safe_Sync_Quellcode.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    archive.write(root / 'build.py','build.py')
    for path in sorted(source.iterdir()):
        if path.is_file():
            if path.name=='config.json':
                archive.writestr('notion_safe_sync/config.json',json.dumps({'NOTION_TOKEN':'','PAGES':[]}))
            else:
                archive.write(path, 'notion_safe_sync/' + path.name)
for name in ('PRUEFBERICHT_'+version+'.md','ANLEITUNG_'+'.'.join(version.split('.')[:2])+'.md'):
    if (source/name).exists(): shutil.copy2(source/name,release/name)
print('Build erstellt: ' + version)
