from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile

APP_DIR = Path.home() / '.winforge'
DB_PATH = APP_DIR / 'snapshots.sqlite3'


def format_size(n: int) -> str:
    unit = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    value = float(n)
    for u in unit:
        if abs(value) < 1024 or u == unit[-1]:
            return f'{value:,.2f} {u}'
        value /= 1024
    return str(n)


def drive_space(path: Path) -> dict:
    usage = shutil.disk_usage(path)
    return dict(total=usage.total, used=usage.used, free=usage.free)


def folder_size(path: Path) -> tuple[int, int, int]:
    total, files, errors = 0, 0, 0
    def onerror(_):
        nonlocal errors
        errors += 1
    for root, dirs, filenames in os.walk(path, followlinks=False, onerror=onerror):
        dirs[:] = [d for d in dirs if not (Path(root)/d).is_symlink()]
        for name in filenames:
            item = Path(root) / name
            try:
                if item.is_symlink():
                    continue
                total += item.stat().st_size
                files += 1
            except OSError:
                errors += 1
    return total, files, errors


def scan(path: Path) -> dict:
    path = path.expanduser().resolve(strict=True)
    if not path.is_dir():
        raise ValueError('Scan target must be a directory')
    children = []
    for child in path.iterdir():
        if child.is_symlink():
            continue
        if child.is_dir():
            size, files, errors = folder_size(child)
        else:
            try:
                size, files, errors = child.stat().st_size, 1, 0
            except OSError:
                size, files, errors = 0, 0, 1
        children.append(dict(name=child.name, path=str(child), logical_bytes=size, files=files, errors=errors))
    children.sort(key=lambda item: item['logical_bytes'], reverse=True)
    return dict(root=str(path), timestamp=dt.datetime.now(dt.timezone.utc).isoformat(), drive=drive_space(path), entries=children)


def connect() -> sqlite3.Connection:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute('CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, created TEXT NOT NULL, root TEXT NOT NULL, payload TEXT NOT NULL)')
    return con


def save_snapshot(data: dict) -> int:
    with connect() as con:
        cur = con.execute('INSERT INTO snapshots(created, root, payload) VALUES(?,?,?)', (data['timestamp'], data['root'], json.dumps(data)))
        return int(cur.lastrowid)


def snapshots() -> list[dict]:
    with connect() as con:
        rows = con.execute('SELECT id,created,root FROM snapshots ORDER BY id DESC').fetchall()
    return [dict(id=r[0], created=r[1], root=r[2]) for r in rows]


def compare(first: int, second: int) -> dict:
    with connect() as con:
        rows = [con.execute('SELECT payload FROM snapshots WHERE id=?', (i,)).fetchone() for i in (first, second)]
    if any(row is None for row in rows):
        raise ValueError('Snapshot ID not found')
    old, new = [json.loads(row[0]) for row in rows]
    if old['root'].casefold() != new['root'].casefold():
        raise ValueError('Compare snapshots of the same directory only')
    before = {e['name']: e['logical_bytes'] for e in old['entries']}
    after = {e['name']: e['logical_bytes'] for e in new['entries']}
    changes = [dict(name=k, before=before.get(k,0), after=after.get(k,0), delta=after.get(k,0)-before.get(k,0)) for k in before.keys()|after.keys()]
    changes.sort(key=lambda e: abs(e['delta']), reverse=True)
    return dict(root=old['root'], changes=changes, free_delta=new['drive']['free']-old['drive']['free'], before_free=old['drive']['free'], after_free=new['drive']['free'])


def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def transfer(src: Path, dst: Path, apply: bool=False) -> dict:
    src=src.expanduser().resolve(strict=True)
    dst=dst.expanduser().absolute()
    if not src.is_file() or src.is_symlink():
        raise ValueError('Only regular files are supported in v0.1')
    if dst.exists():
        raise FileExistsError('Destination already exists; overwriting is disabled')
    if src == dst:
        raise ValueError('Source and destination are the same')
    size=src.stat().st_size
    result=dict(source=str(src), destination=str(dst), size=size, applied=False, verified=False)
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Create destination exclusively; never overwrite an existing file.
        try:
            with src.open('rb') as inp, dst.open('xb') as out:
                shutil.copyfileobj(inp, out, length=1024*1024)
            shutil.copystat(src, dst)
            result['verified'] = sha256(src)==sha256(dst)
            if not result['verified']:
                raise IOError('Hash verification failed: check the destination file')
            result['applied'] = True
        except Exception:
            # Incomplete copy is deliberately left for inspection instead of deleting unseen data.
            raise
    return result


def temp_candidates(days: int=7, base: Path | None = None) -> dict:
    if days < 1:
        raise ValueError('days must be >= 1')
    base = base or Path(tempfile.gettempdir())
    base=base.expanduser().resolve(strict=True)
    cutoff=dt.datetime.now().timestamp()-days*86400
    candidates=[]
    for child in base.iterdir():
        try:
            if child.is_symlink() or not child.is_file():
                continue
            st=child.stat()
            if st.st_mtime < cutoff:
                candidates.append(dict(name=child.name, path=str(child), size=st.st_size))
        except OSError:
            continue
    candidates.sort(key=lambda c:c['size'], reverse=True)
    return dict(root=str(base), days=days, candidates=candidates, total=sum(c['size'] for c in candidates))
