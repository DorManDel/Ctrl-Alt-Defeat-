"""Adapters for *existing* third-party Windows terminal games.

The games are independently licensed and NOT distributed with this project.
Elevated execution is blocked. Game binaries must be selected by the user.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys

@dataclass(frozen=True)
class Game:
    key:str
    name:str
    executable:str
    project:str
    notes:str

GAMES=(
    Game('snake','Snake — rs_snake','rs_snake.exe','https://github.com/baurst/rs_snake/releases', 'MIT; Windows release binary'),
    Game('invaders','Space Invaders — RetroArcade','cinv.exe','https://github.com/fastrgv/RetroArcade/releases', 'GPLv3; extract official 7z, find bin\\win\\cinv.exe'),
)


def game_dir() -> Path:
    return Path.home()/'.ctrl_alt_defeat'/'arcade'


def is_admin() -> bool:
    if os.name!='nt':return False
    import ctypes
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def find_game(game: Game, folder: Path | None=None) -> Path | None:
    root=folder or game_dir()
    if not root.is_dir():return None
    # Fixed lookup locations; never crawl arbitrary drives or execute random files.
    options=[root/game.executable,root/game.key/game.executable,root/game.key/'bin'/'win'/game.executable]
    for path in options:
        if path.is_file() and not path.is_symlink():return path
    return None


def launch(game: Game, folder: Path | None=None, *, admin_check=is_admin, runner=subprocess.Popen):
    if sys.platform!='win32':
        raise OSError('This prebuilt-game adapter currently targets Windows only')
    if admin_check():
        raise PermissionError('Games cannot run with Administrator privileges. Use PlayArcade.cmd from a standard Windows session.')
    executable=find_game(game,folder)
    if executable is None:
        raise FileNotFoundError(f'{game.name} not installed in {folder or game_dir()}; see {game.project}')
    # No shell=True, no injected arguments. Starts selected existing binary only.
    return runner([str(executable)],cwd=str(executable.parent),creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0))
