from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
from . import core, capacity, translator

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console=Console()
except ImportError:
    console=None


def say(msg):
    if console: console.print(msg)
    else: print(msg)


def table(columns, rows):
    if console:
        t=Table(show_header=True, header_style='bold bright_magenta')
        for title in columns: t.add_column(title)
        for row in rows: t.add_row(*(str(value) for value in row))
        console.print(t)
    else:
        print(' | '.join(columns))
        for row in rows: print(' | '.join(map(str,row)))


def run(args):
    if args.command=='scan':
        if console:
            with console.status('[bold magenta]Scanning filesystem…[/bold magenta]', spinner='dots'):
                data=core.scan(Path(args.path))
        else:
            data=core.scan(Path(args.path))
        sid=core.save_snapshot(data) if args.save else None
        say(f"Scan: {data['root']} | Free: {core.format_size(data['drive']['free'])}" + (f' | Snapshot #{sid}' if sid else ''))
        table(['Entry','Logical size','Files','Errors'], [(e['name'],core.format_size(e['logical_bytes']),e['files'],e['errors']) for e in data['entries'][:args.top]])
        say('[yellow]Logical sizes are not unique allocated bytes; hard links, sparse files, and permissions affect totals.[/yellow]')
    elif args.command=='history':
        table(['ID','Timestamp','Folder'], [(s['id'],s['created'],s['root']) for s in core.snapshots()])
    elif args.command=='compare':
        data=core.compare(args.before,args.after)
        say(f"Free-space change: {core.format_size(data['free_delta'])}")
        table(['Directory','Before','After','Delta'], [(e['name'],core.format_size(e['before']),core.format_size(e['after']),f"{e['delta'] / 1024**3:+.3f} GiB") for e in data['changes'][:args.top]])
    elif args.command in ('copy','backup'):
        src,dst=Path(args.source),Path(args.destination)
        if args.command=='backup' and dst.exists() and dst.is_dir():
            dst=dst/src.name
        result=core.transfer(src,dst,apply=args.apply)
        say(('COPIED & SHA256 VERIFIED' if result['applied'] else 'DRY RUN — no changes') + f" | {core.format_size(result['size'])}\n{result['source']}\n  -> {result['destination']}")
    elif args.command=='temp-preview':
        d=core.temp_candidates(args.days)
        say(f"Read-only temp preview: {d['root']} | {len(d['candidates'])} candidate files | {core.format_size(d['total'])}")
        table(['File','Logical size'],[(c['name'],core.format_size(c['size'])) for c in d['candidates'][:args.top]])
        say('[yellow]No deletion is implemented in v0.1. Files may be active even when old.[/yellow]')
    elif args.command=='doctor':
        say('Ctrl+Alt+Defeat doctor (read-only)')
        paths=[Path(os.environ.get('LOCALAPPDATA',Path.home()))/'ollama', Path(os.environ.get('PROGRAMFILES(X86)','C:/Program Files (x86)'))/'Steam'/'steamapps'/'downloading']
        for p in paths:
            say(f"{'FOUND' if p.exists() else 'NOT FOUND'}: {p}")
        say(f"Snapshot DB: {core.DB_PATH}")
    elif args.command=='capacity-test':
        data=capacity.probe(Path(args.path),mib=args.mib,mode=args.mode,
                            apply=args.apply,cleanup=args.cleanup)
        for k,v in data.items():say(f'{k}: {v}')
        if not args.apply:say('[yellow]PREVIEW ONLY. For execution add --apply. System drive is blocked.[/yellow]')
    elif args.command=='capacity-cleanup':
        say(capacity.cleanup_test(Path(args.path)))
    elif args.command=='translate':
        out=translator.suggest(' '.join(args.request) if isinstance(args.request,list) else args.request)
        say(f"{out['description']}\n{out['command'] or '(none)'}\n{out['notice']}")
    elif args.command=='arcade':
        arcade()
    elif args.command=='menu':
        menu()


def interactive_transfer(action):
    src=input('Source file > ').strip().strip('"')
    dst=input('Destination path > ').strip().strip('"')
    preview=core.transfer(Path(src),Path(dst),apply=False)
    say(f"PREVIEW: {core.format_size(preview['size'])}\n  {preview['source']}\n  -> {preview['destination']}")
    confirm=input('Type COPY to execute and verify SHA256 (anything else cancels) > ').strip()
    if confirm != 'COPY':
        say('Cancelled. No files modified.')
        return
    run(argparse.Namespace(command=action,source=src,destination=dst,apply=True))


GAMES = [
    ('Snake (MIT)', 'https://github.com/GeorgeZhukov/python-snake'),
    ('Space Invaders (RetroArcade)', 'https://github.com/fastrgv/RetroArcade'),
]

def arcade():
    say('[bold magenta]ARCADE // curated third-party games[/bold magenta]')
    table(['Key','Game','Verified project'],[(i+1,n,url) for i,(n,url) in enumerate(GAMES)])
    say('[yellow]Games are NOT bundled or executed in this alpha; review project licenses and releases before installing.[/yellow]')


def menu():
    while True:
        say('\n[bold bright_magenta]◆ CTRL+ALT+DEFEAT[/bold bright_magenta] [yellow]// TERMINAL TOOLKIT[/yellow]')
        table(['Key','Module'],[('1','Storage scan + snapshot'),('2','Compare snapshots'),('3','Snapshot history'),('4','Temp candidates (read-only)'),('5','Copy file (preview + confirm)'),('6','System doctor'),('7','Backup file (preview + confirm)'),('8','Capacity test (bounded / external drive)'),('9','Command translator (preview only)'),('A','Arcade game links'),('0','Exit')])
        choice=input('Choose > ').strip()
        try:
            if choice=='0':return
            if choice=='1':run(argparse.Namespace(command='scan',path=input('Path to scan > ').strip(),save=True,top=15))
            elif choice=='2':run(argparse.Namespace(command='compare',before=int(input('Older ID > ')),after=int(input('Newer ID > ')),top=20))
            elif choice=='3':run(argparse.Namespace(command='history'))
            elif choice=='4':run(argparse.Namespace(command='temp-preview',days=7,top=20))
            elif choice=='5':interactive_transfer('copy')
            elif choice=='7':interactive_transfer('backup')
            elif choice=='6':run(argparse.Namespace(command='doctor'))
            elif choice=='8':
                path=input('Existing target folder (NOT C:) > ').strip().strip('\"')
                mib=int(input('Test MiB (1-4096; default 64) > ').strip() or '64')
                mode=input('random or zeros [random] > ').strip().lower() or 'random'
                run(argparse.Namespace(command='capacity-test',path=path,mib=mib,mode=mode,apply=False,cleanup=False))
                if input('Type TEST to write/verify and remove OWNED test files > ').strip()=='TEST':
                    run(argparse.Namespace(command='capacity-test',path=path,mib=mib,mode=mode,apply=True,cleanup=True))
            elif choice=='9':
                run(argparse.Namespace(command='translate',request=input('Describe desired task > ')))
            elif choice.lower()=='a':arcade()
            else:say('Unknown selection')
        except (OSError, ValueError) as exc:say(f'[red]Error: {exc}[/red]')


def parser():
    p=argparse.ArgumentParser(prog='ctrl-alt-defeat',description='Safe, modular Windows-first CLI multitool')
    sub=p.add_subparsers(dest='command',required=True)
    scan=sub.add_parser('scan',help='Read-only immediate-child size inventory')
    scan.add_argument('path');scan.add_argument('--save',action='store_true');scan.add_argument('--top',type=int,default=20)
    sub.add_parser('history')
    c=sub.add_parser('compare');c.add_argument('before',type=int);c.add_argument('after',type=int);c.add_argument('--top',type=int,default=20)
    for name in ('copy','backup'):
        a=sub.add_parser(name);a.add_argument('source');a.add_argument('destination');a.add_argument('--apply',action='store_true',help='Explicitly perform verified file copy')
    temp=sub.add_parser('temp-preview');temp.add_argument('--days',type=int,default=7);temp.add_argument('--top',type=int,default=20)
    cap=sub.add_parser('capacity-test',help='Bounded write/read test. Blocked on Windows system drive.')
    cap.add_argument('path');cap.add_argument('--mib',type=int,default=64)
    cap.add_argument('--mode',choices=['random','zeros'],default='random')
    cap.add_argument('--apply',action='store_true');cap.add_argument('--cleanup',action='store_true')
    cc=sub.add_parser('capacity-cleanup',help='Remove only owned, manifest-listed test files')
    cc.add_argument('path')
    tr=sub.add_parser('translate',help='Suggest a vetted command, never execute')
    tr.add_argument('request',nargs='+')
    sub.add_parser('arcade')
    sub.add_parser('doctor');sub.add_parser('menu')
    return p


def main():
    args=parser().parse_args()
    try:run(args)
    except (OSError,ValueError) as exc:
        say(f'[red]Error: {exc}[/red]');sys.exit(1)

if __name__=='__main__':main()
