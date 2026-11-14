"""Bounded back-stack for terminal UI locations (never cancels jobs)."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Location:
    module: int
    focus: str
    folder: Path
    drive_mode: bool
    cursor: int


class NavigationStack:
    def __init__(self, limit: int = 64):
        if limit < 1:
            raise ValueError('Navigation history limit must be positive')
        self.limit = limit
        self._past: list[Location] = []

    @property
    def depth(self) -> int:
        return len(self._past)

    def remember(self, location: Location) -> None:
        if not self._past or self._past[-1] != location:
            self._past.append(location)
            del self._past[:-self.limit]

    def back(self) -> Location | None:
        return self._past.pop() if self._past else None
