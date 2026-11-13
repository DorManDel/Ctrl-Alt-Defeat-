"""Best-effort console and terminal-tab titles.

No subprocesses, privilege changes or network calls. SetConsoleTitleW is used for
Windows console hosts and OSC 0 for terminal emulators that accept title updates.
Windows Terminal can ignore app titles via suppressApplicationTitle.
"""
from __future__ import annotations

import os
import re
import sys

APP_NAME = 'Ctrl+Alt+Defeat'
MAX_ACTIVITY_LENGTH = 32


def _safe_label(value: str, limit: int) -> str:
    # Never put control characters, path secrets or arbitrary terminal escapes
    # into a console/tab title; only display bounded job *names*.
    clean = re.sub(r'[^\w +.\-/]', ' ', str(value), flags=re.UNICODE)
    return ' '.join(clean.split())[:limit].strip()


def make_title(state: str = 'READY', activity: str = '', *,
               version: str = '0.5.2-dev') -> str:
    status = _safe_label(state.upper(), 12) or 'READY'
    if status not in {'READY', 'QUEUED', 'RUNNING', 'CANCELLING',
                      'CANCELLED', 'COMPLETED', 'FAILED'}:
        status = 'READY'
    label = f'{APP_NAME} [{status}]'
    if status in {'QUEUED', 'RUNNING', 'CANCELLING'}:
        detail = _safe_label(activity, MAX_ACTIVITY_LENGTH)
        if detail:
            label += f' {detail}'
    return f'{label} | v{_safe_label(version, 24)}'


class TerminalTitle:
    """Only emit changes; restore the previous console title on normal exit."""

    def __init__(self, *, stream=None, windows: bool | None = None, kernel=None):
        self.stream = sys.stdout if stream is None else stream
        self.windows = os.name == 'nt' if windows is None else windows
        self.kernel = kernel
        self.previous: str | None = None
        self.current: str | None = None
        self.started = False

    def start(self):
        if self.started:
            return
        self.started = True
        if not self.windows:
            return
        try:
            import ctypes
            if self.kernel is None:
                self.kernel = ctypes.windll.kernel32
            buffer = ctypes.create_unicode_buffer(512)
            if self.kernel.GetConsoleTitleW(buffer, len(buffer)):
                self.previous = buffer.value
        except (AttributeError, OSError, TypeError):
            pass

    def _set(self, title: str):
        if self.windows and self.kernel is not None:
            try:
                self.kernel.SetConsoleTitleW(title)
            except (AttributeError, OSError, TypeError):
                pass
        try:
            if self.stream.isatty():
                self.stream.write('\x1b]0;' + title + '\x07')
                self.stream.flush()
        except (AttributeError, OSError, ValueError):
            pass

    def update(self, state: str = 'READY', activity: str = '', *,
               version: str = '0.5.2-dev'):
        if not self.started:
            self.start()
        title = make_title(state, activity, version=version)
        if title != self.current:
            self._set(title)
            self.current = title

    def restore(self):
        if not self.started:
            return
        if self.previous:
            self._set(self.previous)
        self.current = None
        self.started = False
