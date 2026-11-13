from __future__ import annotations
import datetime as dt
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import stat


def is_linklike(path: Path) -> bool:
    """Skip symlinks and Windows junction/reparse points during recursive scans."""
    try:
        st = path.lstat()
        return path.is_symlink() or bool(getattr(st, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))
    except OSError:
        return True

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


def folder_size(path: Path, progress=None, cancel_event=None) -> tuple[int, int, int]:
    """Walk without following links, reporting live file progress and safe cancel points."""
    from .jobs import Cancelled
    total, files, errors = 0, 0, 0
    def check():
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled('Scan stopped by user')
    def onerror(_):
        nonlocal errors
        errors += 1
    for root, dirs, filenames in os.walk(path, followlinks=False, onerror=onerror):
        check()
        dirs[:] = [d for d in dirs if not is_linklike(Path(root)/d)]
        for name in filenames:
            check()
            item = Path(root) / name
            try:
                if is_linklike(item):
                    continue
                size = item.stat().st_size
                total += size
                files += 1
                if progress is not None:
                    progress(files=1, bytes_processed=size, current=str(item))
            except OSError:
                errors += 1
    return total, files, errors


def scan(path: Path, progress=None, cancel_event=None) -> dict:
    """Top-level snapshot; percentage denotes completed immediate children, not bytes."""
    from .jobs import Cancelled
    path = path.expanduser().resolve(strict=True)
    if not path.is_dir():
        raise ValueError('Scan target must be a directory')
    children = []
    names = [p for p in path.iterdir() if not is_linklike(p)]
    if progress is not None:
        progress(total=len(names), current=str(path))
    for child in names:
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled('Scan stopped by user')
        if progress is not None:
            progress(current=str(child))
        if child.is_dir():
            size, files, errors = folder_size(child, progress=progress, cancel_event=cancel_event)
        else:
            try:
                size, files, errors = child.stat().st_size, 1, 0
                if progress is not None:
                    progress(files=1, bytes_processed=size)
            except OSError:
                size, files, errors = 0, 0, 1
        children.append(dict(name=child.name, path=str(child), logical_bytes=size, files=files, errors=errors))
        if progress is not None:
            progress(completed=1)
    children.sort(key=lambda item: item['logical_bytes'], reverse=True)
    return dict(root=str(path), timestamp=dt.datetime.now(dt.timezone.utc).isoformat(), drive=drive_space(path), entries=children)


@contextmanager
def connect():
    """Yield a snapshot connection and close its file handle on all platforms.

    sqlite3.Connection's own context manager commits/rolls back, but it does
    *not* close the connection. Windows refuses to delete a DB with open handles.
    """
    APP_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute('CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, created TEXT NOT NULL, root TEXT NOT NULL, payload TEXT NOT NULL)')
        with con:
            yield con
    finally:
        con.close()

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
