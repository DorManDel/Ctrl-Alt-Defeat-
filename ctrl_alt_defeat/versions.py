"""Discovery and cautious recycling of obsolete Ctrl+Alt+Defeat *copies*.

Never follows directory symlinks. Never touches the active installation, Git
checkouts, directories without a recognizable package, or arbitrary parent paths.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import re
import sys

HERE = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r'(?:VERSION\s*=\s*[\'\"]|v)(\d+\.\d+(?:\.\d+)?)', re.I)

@dataclass(frozen=True)
class Candidate:
    path: Path
    version: str
    bytes_estimate: int


def _linked(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def _version(folder: Path) -> str | None:
    """Only recognize an extracted project, never arbitrary matching names."""
    if not folder.is_dir() or _linked(folder) or (folder / '.git').exists():
        return None
    if not (folder / 'ctrl_alt_defeat' / '__main__.py').is_file():
        return None
    if not (folder / 'CtrlAltDefeat.cmd').is_file():
        return None
    vfile=folder/'VERSION.txt'
    if vfile.is_file():
        content=vfile.read_text(encoding='utf-8',errors='replace')[:100]
        m=re.search(r'(\d+\.\d+(?:\.\d+)?)',content)
        if m:return m.group(1)
    dash=folder/'ctrl_alt_defeat'/'dashboard.py'
    if dash.is_file():
        m=VERSION_PATTERN.search(dash.read_text(encoding='utf-8',errors='replace')[:2500])
        if m:return m.group(1)
    readme=folder/'README.md'
    if readme.is_file():
        header=readme.read_text(encoding='utf-8',errors='replace')[:800]
        match=re.search(r'(?:status:|by .*?—|prototype)[^\n]*?v(\d+\.\d+(?:\.\d+)?)',header,re.I)
        if match:return match.group(1)
    return None


def version_tuple(value: str) -> tuple[int,...]:
    return tuple(int(x) for x in (value.split('-')[0]).split('.'))


def scan_candidates(current: Path = HERE, roots: list[Path] | None = None, *, current_version: str='0.5.2') -> list[Candidate]:
    current=current.resolve(strict=True)
    roots=roots if roots is not None else [current.parent]
    found=[]
    for root in roots:
        root=Path(root).resolve(strict=True)
        # Sibling-only, bounded and reviewable. No full drive traversal.
        if not root.is_dir():continue
        for folder in list(root.iterdir())[:250]:
            if not folder.is_dir() or _linked(folder):continue
            if folder.resolve()==current:continue
            v=_version(folder)
            if not v:continue
            if version_tuple(v)>=version_tuple(current_version):continue
            total=0
            for directory, dirnames, files in os.walk(folder, followlinks=False):
                dirnames[:]=[x for x in dirnames if not (Path(directory)/x).is_symlink()]
                for name in files:
                    item=Path(directory)/name
                    try:
                        if not item.is_symlink():total+=item.stat().st_size
                    except OSError:pass
            found.append(Candidate(folder.resolve(),v,total))
    return sorted({x.path:x for x in found}.values(), key=lambda x:(version_tuple(x.version),str(x.path)))


def recycle_candidate(candidate: Candidate, *, current: Path=HERE, recycler=None) -> None:
    """Re-validate before disposing. `recycler` injection permits safe testing."""
    source=candidate.path
    current=current.resolve(strict=True)
    if _linked(source) or source.resolve()==current:
        raise ValueError('Never remove the running version')
    if source.parent.resolve()!=current.parent.resolve():
        raise ValueError('Only sibling installations can be recycled')
    v=_version(source)
    if not v or v!=candidate.version:
        raise ValueError('The folder changed or is not a recognized older installation')
    if version_tuple(v)>=version_tuple(_version(current) or '0.5.2'):
        raise ValueError('Candidate is not older than the running version')
    if recycler is not None:
        recycler(source);return
    if sys.platform!='win32':
        raise OSError('Windows Recycle Bin integration is only available on Windows')
    # Windows shell delete with FOF_ALLOWUNDO and no UI. No permanent deletion.
    import ctypes
    from ctypes import wintypes
    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_=[('hwnd',wintypes.HWND),('wFunc',wintypes.UINT),
                  ('pFrom',wintypes.LPCWSTR),('pTo',wintypes.LPCWSTR),
                  ('fFlags',wintypes.WORD),('fAnyOperationsAborted',wintypes.BOOL),
                  ('hNameMappings',ctypes.c_void_p),('lpszProgressTitle',wintypes.LPCWSTR)]
    op=SHFILEOPSTRUCTW(None,3,str(source)+'\0\0',None,0x0040|0x0010|0x0004,False,None,None)
    code=ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if code or op.fAnyOperationsAborted:
        raise OSError(f'Recycle Bin operation did not complete: {code}')
