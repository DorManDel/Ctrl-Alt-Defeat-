"""Cooperative background operations, timestamps and audit logs.

No forced thread termination. Every destructive action must provide safe cancellation
boundaries. One active operation at a time avoids uncontrolled disk contention.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import threading
import time
import uuid


class Cancelled(Exception):
    """An operation stopped at a safe checkpoint."""


LOG_DIR = Path.home() / '.ctrl_alt_defeat' / 'logs'


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec='seconds')


@dataclass
class Job:
    name: str
    target: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    started: float = field(default_factory=time.monotonic)
    state: str = 'QUEUED'
    completed: int = 0
    total: int | None = None
    files: int = 0
    bytes_processed: int = 0
    current: str = ''
    message: str = ''
    result: object = None
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)
    thread: threading.Thread | None = field(default=None, repr=False)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started

    @property
    def percent(self) -> float | None:
        return (100 * min(self.completed, self.total) / self.total) if self.total else None


class JobManager:
    def __init__(self, log_dir: Path | None = None):
        self.log_dir = log_dir or LOG_DIR
        self.lock = threading.RLock()
        self.current: Job | None = None
        self.events: list[dict] = []

    def log(self, level: str, message: str, job: Job | None = None) -> dict:
        event = {'timestamp': timestamp(), 'level': level, 'message': message,
                 'job_id': job.id if job else None, 'operation': job.name if job else None}
        with self.lock:
            self.events.append(event)
            self.events[:] = self.events[-250:]
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.log_dir / (datetime.now().strftime('%Y-%m-%d') + '.jsonl')
            with log_path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        return event

    def start(self, name: str, target: str, operation) -> Job:
        with self.lock:
            if self.current and self.current.state in {'QUEUED', 'RUNNING', 'CANCELLING'}:
                raise RuntimeError('An operation is already running')
            job = Job(name=name, target=target)
            self.current = job
            self.log('INFO', f'Queued {name}: {target}', job)

        def runner():
            with self.lock:
                job.state = 'RUNNING'
            self.log('INFO', f'Started {name}', job)
            try:
                result = operation(job, self)
                if job.cancel_event.is_set():
                    raise Cancelled('Cancellation requested')
                with self.lock:
                    job.result = result
                    job.state = 'COMPLETED'
                    job.message = 'Completed successfully'
                self.log('SUCCESS', f'{name} completed', job)
            except Cancelled as exc:
                with self.lock:
                    job.state = 'CANCELLED'
                    job.message = str(exc)
                self.log('WARN', f'{name} cancelled: {exc}', job)
            except Exception as exc:
                with self.lock:
                    job.state = 'FAILED'
                    job.message = f'{type(exc).__name__}: {exc}'
                self.log('ERROR', job.message, job)
        t = threading.Thread(target=runner, name=f'cad-{job.id}', daemon=True)
        job.thread = t
        t.start()
        return job

    def cancel(self) -> bool:
        with self.lock:
            if not self.current or self.current.state not in {'QUEUED', 'RUNNING'}:
                return False
            self.current.cancel_event.set()
            self.current.state = 'CANCELLING'
            self.log('WARN', 'Cancellation requested; waiting for safe checkpoint', self.current)
            return True

    def checkpoint(self, job: Job, *, current: str | None = None, files: int = 0,
                   bytes_processed: int = 0, completed: int = 0, total: int | None = None):
        if job.cancel_event.is_set():
            raise Cancelled('Stopped at safe checkpoint')
        with self.lock:
            if current is not None:
                job.current = current
            job.files += files
            job.bytes_processed += bytes_processed
            job.completed += completed
            if total is not None:
                job.total = total


def scan_operation(path: Path, *, persist: bool = True):
    """Return a cancellable recursive inventory worker for immediate children."""
    from . import core
    def operation(job: Job, mgr: JobManager):
        def progress(**kwargs):
            mgr.checkpoint(job, **kwargs)
        data = core.scan(path, progress=progress, cancel_event=job.cancel_event)
        mgr.checkpoint(job)
        if persist:
            number = core.save_snapshot(data)
            mgr.log('INFO', f'Snapshot #{number} saved for {path}', job)
            data['snapshot_id'] = number
        return data
    return operation


def copy_operation(source: Path, destination: Path, chunk_size: int = 1024 * 1024):
    """Verified, non-overwriting copy. On cancel, removes only its own partial file."""
    from . import core
    source = Path(source)
    destination = Path(destination)
    def operation(job: Job, mgr: JobManager):
        if source.expanduser().is_symlink():
            raise ValueError('Symlink sources are not supported')
        src = source.expanduser().resolve(strict=True)
        dest = destination.expanduser().absolute()
        if not src.is_file():
            raise ValueError('Source must be an ordinary file')
        if dest.exists() or src == dest:
            raise FileExistsError('Destination exists or is source; no overwrites allowed')
        size = src.stat().st_size
        job.total = size
        dest.parent.mkdir(parents=True, exist_ok=True)
        created = False
        digest = hashlib.sha256()
        try:
            with src.open('rb') as inp, dest.open('xb') as out:
                created = True
                while True:
                    mgr.checkpoint(job)
                    chunk = inp.read(chunk_size)
                    if not chunk:
                        break
                    out.write(chunk)
                    digest.update(chunk)
                    mgr.checkpoint(job, current=src.name, bytes_processed=len(chunk), completed=len(chunk))
                out.flush(); os.fsync(out.fileno())
            mgr.checkpoint(job)
            if digest.hexdigest() != core.sha256(dest):
                raise IOError('SHA-256 verification failed')
            return {'source': str(src), 'destination': str(dest), 'bytes': size, 'verified': True}
        except Exception:
            # Do not delete unrelated files: this destination was created exclusively by this operation.
            if created:
                try: dest.unlink(missing_ok=True)
                except OSError: pass
            raise
    return operation


def temp_cleanup_operation(report: dict):
    from . import cleanup
    def operation(job: Job, mgr: JobManager):
        files = report['files']
        job.total = len(files)
        deleted = skipped = bytes_removed = 0
        for entry in files:
            mgr.checkpoint(job, current=entry['name'])
            partial = cleanup.delete_user_temp({'root': report['root'], 'files': [entry]})
            deleted += partial['deleted']
            skipped += partial['skipped']
            bytes_removed += partial['bytes']
            mgr.checkpoint(job, completed=1, files=1, bytes_processed=partial['bytes'])
        mgr.log('INFO', f'Deleted {deleted}; skipped {skipped}; logical bytes {bytes_removed}', job)
        return {'deleted': deleted, 'skipped': skipped, 'bytes': bytes_removed}
    return operation
