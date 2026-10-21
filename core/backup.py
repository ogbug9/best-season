"""Consistent DB export plus original/user media; no secrets in manifests."""
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tarfile
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def export_database(path):
    config = settings.DATABASES['default']
    if config['ENGINE'].endswith('sqlite3'):
        source = sqlite3.connect(f"file:{Path(config['NAME']).resolve().as_posix()}?mode=ro", uri=True)
        try:
            with closing(sqlite3.connect(path)) as destination:
                source.backup(destination)
        finally:
            source.close()
        return 'sqlite'
    if not config['ENGINE'].endswith('postgresql'):
        raise CommandError('Поддерживаются PostgreSQL и SQLite.')
    executable = shutil.which('pg_dump')
    if not executable:
        raise CommandError('pg_dump отсутствует; нужен PostgreSQL client в среде резервирования.')
    environment = os.environ.copy()
    for key, name in (('PGHOST', 'HOST'), ('PGPORT', 'PORT'), ('PGUSER', 'USER'), ('PGPASSWORD', 'PASSWORD'), ('PGDATABASE', 'NAME')):
        environment[key] = str(config.get(name) or '')
    result = subprocess.run([executable, '--format=custom', '--no-owner', '--no-acl', '--file', str(path)],
                            env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode:
        raise CommandError('pg_dump завершился с ошибкой. Проверьте подключение и совместимость версий; секреты не выводятся.')
    return 'postgresql'


def create_backup(root, keep=7):
    root = Path(root).resolve()
    media = Path(settings.MEDIA_ROOT).resolve()
    if root == media or root.is_relative_to(media):
        raise CommandError('Каталог копий должен быть вне MEDIA_ROOT.')
    if keep < 7:
        raise CommandError('Нужно хранить минимум семь полных копий.')
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = root / f'.pending-bs-{timestamp}'
    folder.mkdir(mode=0o700)
    kind = export_database(folder / 'database.dump')
    with tarfile.open(folder / 'media.tar.gz', 'w:gz') as archive:
        if media.exists():
            # Follow neither symlinks nor paths outside the user media directory.
            for path in sorted(media.rglob('*')):
                if path.is_file() and not path.is_symlink():
                    archive.add(path, arcname=path.relative_to(media).as_posix(), recursive=False)
    manifest = {'format': 1, 'created_utc': timestamp, 'database': kind,
                'files': {name: {'sha256': digest(folder/name), 'bytes': (folder/name).stat().st_size}
                          for name in ('database.dump', 'media.tar.gz')}}
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    # Validate before atomically declaring the backup complete or pruning.
    verify_backup(folder)
    complete = root / f'bs-{timestamp}'
    folder.rename(complete)
    copies = sorted(p for p in root.glob('bs-*') if p.is_dir() and (p/'manifest.json').is_file())
    for old in copies[:-keep]:
        resolved = old.resolve()
        if resolved.parent != root or old.is_symlink():
            raise CommandError('Некорректный путь старой копии; удаление отменено.')
        shutil.rmtree(resolved)
    return complete


def verify_backup(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format') != 1 or set(manifest['files']) != {'database.dump', 'media.tar.gz'}:
        raise CommandError('Неподдерживаемый формат копии.')
    for name, expected in manifest['files'].items():
        path = folder/name
        if path.is_symlink() or digest(path) != expected['sha256'] or path.stat().st_size != expected['bytes']:
            raise CommandError(f'Повреждён файл копии: {name}.')
    with tarfile.open(folder/'media.tar.gz', 'r:gz') as archive:
        for item in archive:
            destination = (folder/item.name).resolve()
            if not destination.is_relative_to(folder) or not item.isfile():
                raise CommandError('Некорректный путь в media-архиве.')
    if manifest['database'] == 'sqlite':
        with closing(sqlite3.connect(f'file:{(folder/"database.dump").as_posix()}?mode=ro', uri=True)) as connection:
            if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise CommandError('Нарушена целостность SQLite.')
    return manifest
