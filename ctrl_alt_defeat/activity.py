"""Structured local audit journal for app navigation and *proposed* AI plans.

This is not a Windows-wide activity recorder. Source prompts, file paths and
model outputs are deliberately not copied to this journal by default.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
import threading

ALLOWED_EVENTS = frozenset({'navigation', 'plan_prepared', 'plan_failed'})


class ActivityJournal:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else Path.home()/'.ctrl_alt_defeat'/'activity.jsonl'
        self._lock = threading.Lock()

    def record(self, event: str, *, operation: str = '', risk: str = '',
               provider: str = '', executed: bool = False) -> dict:
        if event not in ALLOWED_EVENTS:
            raise ValueError('Unsupported activity event')
        if executed:
            # No executor is connected to this journal. JobManager separately
            # audits real task lifecycle states. Never claim execution here.
            raise ValueError('Use the actual executor log for completed operations')
        row = {
            'timestamp': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'event': event,
            'operation': str(operation)[:80],
            'risk': str(risk)[:32],
            'provider': str(provider)[:48],
            'executed': False,
        }
        with self._lock:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.path.open('a',encoding='utf-8') as handle:
                handle.write(json.dumps(row,ensure_ascii=False)+'\n')
        return row

    def record_plan(self, plan: dict) -> dict:
        return self.record('plan_prepared',operation=plan.get('intent','unknown'),
                           risk=plan.get('risk','unknown'),provider=plan.get('provider','unknown'))

    def recent(self, limit: int = 12) -> list[dict]:
        if not self.path.exists():
            return []
        with self._lock:
            # Bounded memory: read last 128KiB of this local append-only file.
            with self.path.open('rb') as f:
                f.seek(0,2)
                size=f.tell()
                f.seek(max(0,size-131072))
                raw=f.read().decode('utf-8',errors='replace')
            if size>131072:
                raw=raw.split('\n',1)[-1]
            rows=[]
            for line in raw.splitlines()[-max(0,limit):]:
                try:rows.append(json.loads(line))
                except json.JSONDecodeError:continue
            return rows
