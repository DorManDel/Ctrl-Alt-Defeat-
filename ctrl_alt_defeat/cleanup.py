"""Scoped temp cleanup: explicit preview, narrow directory, revalidation before deletion."""
from __future__ import annotations
import datetime as dt
import os
from pathlib import Path
import tempfile


def preview_user_temp(days=7, base=None):
    if days < 1:raise ValueError('Minimum age is one day')
    folder=(Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData'/'Local'))) / 'Temp') if base is None else Path(base)
    folder=folder.resolve(strict=True)
    if not folder.is_dir():raise ValueError('Not a directory')
    # Fixed user temp root in production. Explicit base is only for unit tests.
    if base is None:
        expected=(Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData'/'Local')))/'Temp').resolve(strict=True)
        if folder!=expected:raise ValueError('Temp root validation failed')
    cutoff=dt.datetime.now().timestamp()-days*86400
    found=[]
    for p in folder.iterdir():
        try:
            if p.is_symlink() or not p.is_file():continue
            st=p.stat()
            if st.st_nlink>1 or st.st_mtime>=cutoff:continue
            found.append(dict(name=p.name,path=str(p),size=st.st_size,mtime_ns=st.st_mtime_ns,identity=(st.st_dev,st.st_ino)))
        except OSError:continue
    found.sort(key=lambda p:p['size'],reverse=True)
    return dict(root=str(folder), files=found, bytes=sum(f['size'] for f in found))


def delete_user_temp(report):
    root=Path(report['root']).resolve(strict=True)
    deleted=skipped=bytes_removed=0
    for f in report['files']:
        p=Path(f['path'])
        try:
            if p.parent.resolve(strict=True)!=root or p.is_symlink() or not p.is_file():skipped+=1;continue
            s=p.stat()
            if (s.st_size,s.st_mtime_ns,(s.st_dev,s.st_ino))!=(f['size'],f['mtime_ns'],tuple(f['identity'])) or s.st_nlink>1:
                skipped+=1;continue
            p.unlink()
            deleted+=1;bytes_removed+=s.st_size
        except OSError:skipped+=1
    return dict(deleted=deleted,skipped=skipped,bytes=bytes_removed)
