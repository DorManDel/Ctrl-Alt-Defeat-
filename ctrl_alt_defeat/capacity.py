"""Bounded non-destructive write/read verification inside a new owned directory.

This is NOT secure erasure or a whole-device counterfeit-capacity certification.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import uuid

MIB = 1024**2
GIB = 1024**3
MAX_TEST_MIB = 4096
DEFAULT_RESERVE_MIB = 5120
CHUNK = MIB
PREFIX = '.winforge-capacity-'


def _is_system_drive(target: Path) -> bool:
    """Determine whether an existing Windows target resides on the system drive."""
    if os.name != 'nt':
        return False
    system_drive = os.environ.get('SystemDrive', 'C:').upper().rstrip('\\/')
    return target.drive.upper().rstrip('\\/') == system_drive


def _validate_target(target: Path, mib: int, reserve_mib: int):
    target = target.resolve(strict=True)
    if not target.is_dir() or target.is_symlink():
        raise ValueError('Target must be an existing, real directory')
    if mib < 1 or mib > MAX_TEST_MIB:
        raise ValueError(f'Test must be between 1 and {MAX_TEST_MIB} MiB')
    if reserve_mib < DEFAULT_RESERVE_MIB:
        raise ValueError(f'Minimum reserve is {DEFAULT_RESERVE_MIB} MiB')
    if _is_system_drive(target):
        raise ValueError('Refusing capacity stress test on Windows system drive')
    free = shutil.disk_usage(target).free
    if free < (mib + reserve_mib) * MIB:
        raise ValueError('Not enough free space after retaining safety reserve')
    return target, free


def probe(target: Path, mib: int = 64, mode: str = 'random', *, apply: bool = False,
          reserve_mib: int = DEFAULT_RESERVE_MIB, cleanup: bool = False):
    """Create exclusively owned files, verify SHA256, optionally remove only owned files.

    Recoverable directory is retained on exceptions so the user can inspect it.
    """
    if mode not in ('random', 'zeros'):
        raise ValueError('mode must be random or zeros')
    target, initial_free = _validate_target(Path(target), mib, reserve_mib)
    preview = {'target': str(target), 'requested_mib': mib, 'mode': mode,
               'free_before_bytes': initial_free, 'reserve_mib': reserve_mib,
               'applied': False}
    if not apply:
        return preview
    owned = target / (PREFIX + uuid.uuid4().hex)
    owned.mkdir(mode=0o700)
    manifest = {'schema': 1, 'test_id': owned.name, 'mode': mode, 'created': time.time(), 'files': []}
    total = mib * MIB
    written = 0
    while written < total:
        remaining = min(GIB, total - written)
        filename = f'block-{len(manifest["files"]):04d}.dat'
        path = owned / filename
        sha = hashlib.sha256()
        # Exclusive creation: never overwrite user content.
        with path.open('xb') as file:
            left = remaining
            while left:
                take = min(CHUNK, left)
                data = os.urandom(take) if mode == 'random' else bytes(take)
                file.write(data)
                sha.update(data)
                left -= take
            file.flush()
            os.fsync(file.fileno())
        manifest['files'].append({'name': filename, 'bytes': remaining, 'sha256': sha.hexdigest()})
        (owned / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        written += remaining
    for item in manifest['files']:
        actual = hashlib.sha256()
        with (owned / item['name']).open('rb') as file:
            for chunk in iter(lambda: file.read(CHUNK), b''):
                actual.update(chunk)
        if actual.hexdigest() != item['sha256']:
            raise IOError(f'Verification failed: {item["name"]}; test files retained at {owned}')
    result = dict(preview, applied=True, verified_mib=mib,
                  free_after_write_bytes=shutil.disk_usage(target).free,
                  test_directory=str(owned))
    if cleanup:
        result['cleanup'] = cleanup_test(owned)
    return result


def cleanup_test(directory: Path):
    """Delete only files proven to belong to a Ctrl+Alt+Defeat-owned test directory."""
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir() or not directory.name.startswith(PREFIX):
        raise ValueError('Not a Ctrl+Alt+Defeat test directory')
    manifest_file = directory / 'manifest.json'
    if manifest_file.is_symlink() or not manifest_file.is_file():
        raise ValueError('Missing manifest; refusing deletion')
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    if manifest.get('test_id') != directory.name or manifest.get('schema') != 1:
        raise ValueError('Manifest mismatch; refusing deletion')
    allowed = {'manifest.json'}
    for item in manifest['files']:
        name = item['name']
        if Path(name).name != name or not name.startswith('block-') or not name.endswith('.dat'):
            raise ValueError('Unsafe manifest entry')
        allowed.add(name)
    actual = {p.name for p in directory.iterdir()}
    if actual != allowed or any(p.is_symlink() or not p.is_file() for p in directory.iterdir()):
        raise ValueError('Unknown or changed files found; refusing deletion')
    for item in manifest['files']:
        p = directory / item['name']
        if p.stat().st_size != item['bytes']:
            raise ValueError('Test file size changed; refusing cleanup')
        digest = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(CHUNK), b''):
                digest.update(chunk)
        if digest.hexdigest() != item['sha256']:
            raise ValueError('Test file content changed; refusing cleanup')
    bytes_removed = sum((directory / x).stat().st_size for x in allowed if x != 'manifest.json')
    for name in allowed:
        (directory / name).unlink()
    directory.rmdir()
    return {'removed_test_bytes': bytes_removed, 'directory': str(directory)}
