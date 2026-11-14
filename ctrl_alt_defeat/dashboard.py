"""Ctrl+Alt+Defeat v0.5: dependency-free, two-pane, non-blocking Windows TUI.

The screen is repainted while background jobs run. ANSI VT mode is enabled on
Windows and disabled gracefully when unavailable. No invented byte progress.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import os
import shutil
import string
import sys
import time

from . import core, cleanup, translator, versions, arcade, intent_router
from .navigation import Location, NavigationStack
from .activity import ActivityJournal
from .jobs import JobManager, scan_operation, copy_operation, temp_cleanup_operation

VERSION = '0.5.2-dev'
AUTHOR = 'DorManDel'
MENU = [
    ('Storage Detective', 'DRIVES / FOLDERS / SNAPSHOTS'),
    ('Snapshot History', 'DIFF / RECOVERED SPACE'),
    ('Safe Temp Cleanup', 'PREVIEW / CONFIRM'),
    ('File Operations', 'COPY / BACKUP / SHA256'),
    ('System Doctor', 'READ-ONLY DIAGNOSTICS'),
    ('Command Translator', 'VETTED SUGGESTIONS'),
    ('Arcade', 'EXTERNAL GAMES / NOT INSTALLED'),
    ('Help & Controls', 'SHORTCUTS / SAFETY'),
    ('Event Logs', 'TIMESTAMPED AUDIT TRAIL'),
    ('Version Manager', 'FIND OLDER COPIES / RECYCLE'),
    ('Self-Test', 'STARTUP / MODULE CHECKS'),
    ('Exit', 'RETURN TO WINDOWS'),
]

RESET='\033[0m'
C = {'purple':'\033[38;2;193;153;255m','yellow':'\033[38;2;245;203;113m',
     'cyan':'\033[38;2;114;213;232m','green':'\033[38;2;122;225;172m',
     'red':'\033[38;2;251;114;126m','gray':'\033[38;2;150;162;186m',
     'white':'\033[38;2;237;238;251m'}

def color(text: str, name: str, use_color: bool=True) -> str:
    return C[name] + text + RESET if use_color else text


def shorten(text: str, width: int) -> str:
    if width <= 0: return ''
    text = str(text).replace('\r',' ').replace('\n',' ')
    return text if len(text) <= width else text[:max(0,width-1)]+'…'


def box(title: str, lines: list[str], width: int, height: int, accent='purple',
        use_color=False) -> list[str]:
    """Render exactly `height` rows, `width` columns of content."""
    width=max(12,width);height=max(4,height)
    label = f' {shorten(title.upper(), max(1,width-7))} '
    top = '┌'+label+'─'*max(0,width-2-len(label))+'┐'
    result=[color(top,accent,use_color)]
    for i in range(height-2):
        text=shorten(lines[i] if i<len(lines) else '', width-4)
        result.append(color('│',accent,use_color)+' '+text.ljust(width-4)+' '+color('│',accent,use_color))
    result.append(color('└'+'─'*(width-2)+'┘',accent,use_color))
    return result


# Intentionally hand-verified five-row terminal glyphs; never rely on generated figlet spelling.
GLYPHS = {
    'C': [' ####','##   ','##   ','##   ',' ####'],
    'T': ['#####','  #  ','  #  ','  #  ','  #  '],
    'R': ['#### ','#   #','#### ','#  # ','#   #'],
    'L': ['#    ','#    ','#    ','#    ','#####'],
    'A': [' ### ','#   #','#####','#   #','#   #'],
    'D': ['#### ','#   #','#   #','#   #','#### '],
    'E': ['#####','#    ','#### ','#    ','#####'],
    'F': ['#####','#    ','#### ','#    ','#    '],
    '+': ['  #  ','  #  ','#####','  #  ','  #  '],
}

def ascii_logo(width: int, use_color: bool) -> list[str]:
    """Return five colored, verified lines spelling CTRL + ALT + DEFEAT."""
    parts=[('CTRL','purple'),('+','yellow'),('ALT','cyan'),('+','yellow'),('DEFEAT','green')]
    raw_width=sum(len(word)*6-1 for word,_ in parts)+3*(len(parts)-1)
    pad=' '*max(0,(width-raw_width)//2)
    output=[]
    for row in range(5):
        fragments=[]
        for word,shade in parts:
            plain=' '.join(GLYPHS[ch][row] for ch in word)
            fragments.append(color(plain,shade,use_color))
        output.append(pad+'   '.join(fragments))
    return output

def enumerate_drives() -> list[Path]:
    if os.name!='nt': return [Path('/')]
    return [Path(f'{letter}:\\') for letter in string.ascii_uppercase if Path(f'{letter}:\\').exists()]


def readable_size(n: int | float) -> str:
    return core.format_size(int(n))


def age(seconds: float) -> str:
    return f'{int(seconds//60):02}:{int(seconds%60):02}'


@dataclass
class Prompt:
    label: str
    kind: str
    text: str = ''


class Controller:
    def __init__(self, jobs: JobManager | None = None, path: Path | None = None):
        self.jobs = jobs or JobManager()
        self.mode = 0
        self.focus = 'menu'
        self.menu_cursor = 0
        self.content_cursor = 0
        self.path = path or Path.home()
        self.drive_mode = False
        self.prompt: Prompt | None = None
        self.source = ''
        self.destination = ''
        self.message = 'Ready. Select a module or press F1 for help.'
        self.report: dict | None = None
        self.snapshot_anchor: int | None = None
        self.translation: dict | None = None
        self.intent_plan: dict | None = None
        self.result_mode = 'command'
        self.old_versions: list[versions.Candidate] = []
        self.game_cursor = 0
        self.translator_query = ''
        self.should_exit = False
        self.exit_when_idle = False
        self.last_browser: list[Path] = []
        self.history = NavigationStack()
        self.storage_view = "folders"
        self.activity = ActivityJournal(self.jobs.log_dir.parent/'activity.jsonl')
        self.refresh_content()

    @property
    def current_module(self):
        return MENU[self.mode][0]

    def refresh_content(self):
        if self.mode == 0:
            if self.drive_mode:
                self.last_browser=enumerate_drives()
            else:
                try:
                    self.last_browser = sorted((p for p in self.path.iterdir()
                       if p.is_dir() and not core.is_linklike(p)),key=lambda p:p.name.casefold())[:150]
                except OSError:
                    self.last_browser=[]
        self.content_cursor = max(0,min(self.content_cursor,max(0,len(self.last_browser)-1)))

    def _location(self) -> Location:
        return Location(self.mode, self.focus, self.path, self.drive_mode, self.content_cursor)

    def _remember_location(self):
        self.history.remember(self._location())

    def enter_module(self, number: int):
        if number == len(MENU)-1:
            self.request_exit();return
        if number != self.mode or self.focus != "content":
            self._remember_location()
        self.mode = number
        self.focus = 'content'
        self.content_cursor=0
        if number==0:self.refresh_content()
        if number==9:
            self.refresh_versions()
        if number==2:
            try:
                self.report=cleanup.preview_user_temp(days=7)
                self.message=f"Previewed {len(self.report['files'])} old Temp files; nothing deleted."
            except (OSError, ValueError) as exc:
                self.report=None;self.message=f'Temp preview unavailable: {exc}'
        self.jobs.log('INFO', f'Opened {self.current_module}')
        self.activity.record('navigation', operation=self.current_module)

    def refresh_versions(self):
        try:
            self.old_versions=versions.scan_candidates(
                current=versions.HERE, current_version=VERSION.removesuffix('-dev'))
            self.content_cursor=min(self.content_cursor,max(0,len(self.old_versions)-1))
            self.message=f'{len(self.old_versions)} verified older sibling copies found. Git checkouts are excluded.'
        except (OSError, ValueError) as exc:
            self.old_versions=[]
            self.message=f'Version discovery failed: {exc}'

    def start_selfcheck(self):
        from . import selfcheck
        try:
            job=self.jobs.start('WinForge self-test','local installation',selfcheck.run_checks)
            self.message=f'Self-test #{job.id} started. Browse freely; check status for result.'
        except RuntimeError as exc:self.message=str(exc)

    def request_exit(self):
        job=self.jobs.current
        if job and job.state in ('RUNNING','QUEUED','CANCELLING'):
            self.exit_when_idle=True
            self.jobs.cancel()
            self.message='Stopping active operation first; exiting after safe checkpoint.'
        else:
            self.should_exit=True

    def action_cancel(self):
        if self.jobs.cancel():
            self.message='Cancellation requested. UI remains responsive.'
        elif self.prompt is not None:
            self.prompt=None;self.message='Input cancelled.'
        else:self.message='No active cancellable operation.'

    def action_back(self):
        if self.prompt is not None:
            self.prompt=None;self.message='Input cancelled.';return
        previous = self.history.back()
        if previous is None:
            self.focus='menu'
            self.message='Back to module navigation. Running jobs continue.'
            return
        self.mode = previous.module
        self.focus = previous.focus
        self.path = previous.folder
        self.drive_mode = previous.drive_mode
        self.content_cursor = previous.cursor
        if self.mode == 0:
            self.refresh_content()
        self.message=f'Back to {self.current_module}. Running jobs continue.'
        self.jobs.log('INFO', f'Navigated back to {self.current_module}')
        self.activity.record('navigation', operation=self.current_module)

    def start_scan(self):
        if self.mode!=0:return
        try:
            job=self.jobs.start('Storage scan',str(self.path),scan_operation(self.path))
            self.message=f'Scan #{job.id} launched in background. You can keep browsing.'
        except RuntimeError as exc:self.message=str(exc)

    def start_temp_delete(self):
        if not self.report or not self.report['files']:
            self.message='No eligible Temp files to remove.';return
        self.prompt=Prompt('Type DELETE TEMP to confirm (Esc cancels)', 'delete_temp')

    def confirm_prompt(self, value: str):
        value=value.strip().strip('"')
        kind=self.prompt.kind if self.prompt else ''
        self.prompt=None
        if kind=='goto':
            if not value:return
            path=Path(os.path.expandvars(value)).expanduser()
            if not path.is_dir():self.message='Invalid directory; nothing changed.';return
            self.path=path.resolve();self.drive_mode=False;self.refresh_content();self.message=f'Browsing {self.path}'
        elif kind=='copy_source':
            if value:self.source=value;self.prompt=Prompt('Destination (must NOT exist)', 'copy_dest')
        elif kind=='copy_dest':
            if not value:return
            self.destination=value
            try:
                src=Path(self.source).expanduser().resolve(strict=True)
                dst=Path(self.destination).expanduser().absolute()
                if not src.is_file() or src.is_symlink() or dst.exists() or src==dst:
                    raise ValueError('Invalid source/destination or destination already exists')
                self.message=f'COPY PREVIEW: {readable_size(src.stat().st_size)} to {dst}. Type COPY to approve.'
                self.prompt=Prompt('Type COPY to execute, Esc cancels', 'copy_approve')
            except (OSError,ValueError) as exc:self.message=f'Copy preview rejected: {exc}'
        elif kind=='copy_approve':
            if value!='COPY':self.message='Copy cancelled; no change.';return
            try:
                job=self.jobs.start('SHA256 verified copy',self.source,
                                     copy_operation(Path(self.source),Path(self.destination)))
                self.message=f'Copy #{job.id} started. Navigate freely; C cancels.'
            except RuntimeError as exc:self.message=str(exc)
        elif kind=='delete_temp':
            if value!='DELETE TEMP':self.message='Deletion cancelled; no change.';return
            try:
                job=self.jobs.start('User Temp cleanup',self.report['root'],temp_cleanup_operation(self.report))
                self.message=f'Temp cleanup #{job.id} started. Only previewed eligible files.'
            except RuntimeError as exc:self.message=str(exc)
        elif kind=='translate':
            if value:
                self.result_mode='command';self.intent_plan=None
                self.translation=translator.suggest(value)
                self.translator_query=value
                self.message='Offline translator preview ready. No command was run.'
        elif kind=='intent_offline':
            if value:
                self.result_mode='intent';self.translation=None
                self.translator_query=value
                self.intent_plan=intent_router.offline_demo(value)
                self.activity.record_plan(self.intent_plan)
                self.message='Offline intent baseline ready. No action executed.'
        elif kind=='intent_ollama':
            if value:
                self.result_mode='intent';self.translation=None
                self.translator_query=value
                self.intent_plan=None
                def op(job,mgr):
                    def received(chunk):
                        mgr.checkpoint(job,bytes_processed=len(chunk),current='Receiving structured intent JSON')
                    plan=intent_router.from_ollama(value, cancel_event=job.cancel_event, on_chunk=received)
                    self.activity.record_plan(plan)
                    return plan
                try:
                    job=self.jobs.start('Ollama intent classifier','<local request withheld>',op)
                    self.message=f'Intent classification #{job.id} running; no commands will execute.'
                except RuntimeError as exc:
                    self.message=str(exc)
        elif kind=='translate_ai':
            if value:
                self.result_mode='command';self.intent_plan=None
                self.translator_query=value
                def op(job,mgr):
                    def received(chunk):mgr.checkpoint(job,bytes_processed=len(chunk),current='Streaming local model response')
                    return translator.from_ollama(value,cancel_event=job.cancel_event,on_chunk=received)
                try:
                    job=self.jobs.start('Ollama translator','<local request withheld>',op)
                    self.message=f'Local Ollama request started #{job.id}. ESC returns; C cancels.'
                except RuntimeError as exc:self.message=str(exc)
        elif kind=='recycle_version':
            if value!='RECYCLE':
                self.message='No version removed.';return
            candidate=getattr(self,'chosen_version',None)
            if candidate is None:self.message='No version selected.';return
            try:
                # Synchronous shell operation; no fake claim of cancellation.
                versions.recycle_candidate(candidate)
                self.jobs.log('WARN',f'Recycled old installation: {candidate.path}')
                self.message=f'Recycled: {candidate.path.name}. Check Recycle Bin to restore.'
                self.refresh_versions()
            except (OSError,ValueError) as exc:
                self.message=f'Recycle failed: {exc}'

    def handle_key(self, key: str):
        """Input key names: up/down/enter/esc/back/tab/f1/ctrl+c, or printable characters."""
        if self.prompt:
            if key=='esc':self.action_back()
            elif key=='enter':self.confirm_prompt(self.prompt.text)
            elif key=='back':self.prompt.text=self.prompt.text[:-1]
            elif key=='ctrl+c':self.action_cancel()
            elif len(key)==1 and key.isprintable():self.prompt.text+=key
            return
        if len(key)==1:key=key.lower()
        if key=='ctrl+c':self.action_cancel();return
        if key=='esc':self.action_back();return
        if key=='f1' or key=='?':self.enter_module(7);return
        if key=='tab':self.focus='content' if self.focus=='menu' else 'menu';return
        if key=='c':self.action_cancel();return
        if key=='q':self.request_exit();return
        if key=='l':self.enter_module(8);return
        if self.focus=='menu':
            if key=='up':self.menu_cursor=(self.menu_cursor-1)%len(MENU)
            elif key=='down':self.menu_cursor=(self.menu_cursor+1)%len(MENU)
            elif key=='enter':self.enter_module(self.menu_cursor)
            elif key.isdigit() and key!='0' and int(key)<=len(MENU):self.enter_module(int(key)-1)
            return
        if self.mode==0:
            if key=='s':self.start_scan()
            elif key=='g':self.prompt=Prompt('Go to folder path', 'goto')
            elif key=='d':
                self._remember_location()
                self.drive_mode=True;self.refresh_content();self.message='Choose a drive; Enter to open.'
            elif key=='v':
                self.storage_view='bars' if self.storage_view=='folders' else 'folders'
                self.message='Storage view: '+self.storage_view+' (bars require a completed scan)'
            elif key=='back':
                if self.drive_mode:self.drive_mode=False;self.refresh_content()
                elif self.path.parent!=self.path:
                    self._remember_location()
                    self.path=self.path.parent;self.refresh_content()
            elif key=='up':self.content_cursor=max(0,self.content_cursor-1)
            elif key=='down':self.content_cursor=min(max(0,len(self.last_browser)-1),self.content_cursor+1)
            elif key=='enter' and self.last_browser:
                self._remember_location()
                self.path=self.last_browser[self.content_cursor];self.drive_mode=False
                self.refresh_content();self.message=f'Browsing {self.path}'
        elif self.mode==1:
            rows=core.snapshots()
            if key=='up':self.content_cursor=max(0,self.content_cursor-1)
            elif key=='down':self.content_cursor=min(max(0,len(rows)-1),self.content_cursor+1)
            elif key=='enter' and rows:
                snap=rows[self.content_cursor]
                if self.snapshot_anchor is None:
                    self.snapshot_anchor=snap['id'];self.message=f"Baseline #{snap['id']} selected. Select another snapshot of same root."
                else:
                    try:
                        result=core.compare(self.snapshot_anchor,snap['id'])
                        self.message=f"Difference: free space {readable_size(result['free_delta'])}; {len(result['changes'])} entries."
                        self.translation={'description':f"Snapshot {self.snapshot_anchor} vs #{snap['id']}",
                            'command':'\n'.join(f"{e['delta']/1024**3:+.3f} GiB  {e['name']}" for e in result['changes'][:10]),'notice':'Logical folder deltas; not unique allocated bytes'}
                        self.snapshot_anchor=None
                    except ValueError as exc:self.message=str(exc)
        elif self.mode==2:
            if key=='r':self.enter_module(2)
            elif key=='x':self.start_temp_delete()
        elif self.mode==3 and key=='n':self.prompt=Prompt('Source file', 'copy_source')
        elif self.mode==5:
            if key=='n':self.prompt=Prompt('Describe task (offline curated recipes)', 'translate')
            elif key=='o':self.prompt=Prompt('Describe task (Ollama local AI preview)', 'translate_ai')
            elif key=='i':self.prompt=Prompt('Describe task for Ollama intent planner (no execution)', 'intent_ollama')
            elif key=='p':self.prompt=Prompt('Describe task for offline intent baseline', 'intent_offline')
        elif self.mode==6:
            if key=='up':self.game_cursor=max(0,self.game_cursor-1)
            elif key=='down':self.game_cursor=min(len(arcade.GAMES)-1,self.game_cursor+1)
            elif key=='enter':
                game=arcade.GAMES[self.game_cursor]
                # Never run third-party games with the Administrator token.
                if arcade.is_admin():
                    self.message=f'Use PlayArcade.cmd (non-admin) to play {game.name}. Installed games: {arcade.game_dir()}'
                else:
                    try:
                        arcade.launch(game)
                        self.jobs.log('INFO',f'Launched game {game.name} as standard user')
                        self.message=f'Started {game.name} in a separate console.'
                    except (OSError,PermissionError) as exc:self.message=str(exc)
        elif self.mode==9:
            if key=='r':self.refresh_versions()
            elif key=='up':self.content_cursor=max(0,self.content_cursor-1)
            elif key=='down':self.content_cursor=min(max(0,len(self.old_versions)-1),self.content_cursor+1)
            elif key=='enter' and self.old_versions:
                self.chosen_version=self.old_versions[self.content_cursor]
                self.prompt=Prompt(f'Type RECYCLE to send {self.chosen_version.path.name} to Recycle Bin (could sync to OneDrive)', 'recycle_version')
        elif self.mode==10 and key=='r':self.start_selfcheck()

    def content_lines(self) -> list[str]:
        if self.mode==0:
            rows=['STORAGE / '+('AVAILABLE DRIVES' if self.drive_mode else str(self.path)),
                  'D: drives   G: go to path   S: scan   V: list/bars',
                  '↑↓: select   Enter: open   Backspace: parent   Esc: history', '']
            try:
                usage=shutil.disk_usage(self.path)
                rows.append(f'Disk: {readable_size(usage.free)} free / {readable_size(usage.total)}')
            except OSError:rows.append('Disk usage unavailable')
            rows.append('')
            scan_job=self.jobs.current
            if self.storage_view=='bars':
                if scan_job and scan_job.name=='Storage scan' and scan_job.state=='COMPLETED' and scan_job.result and Path(scan_job.result.get('root','')).resolve()==self.path.resolve():
                    entries=sorted(scan_job.result.get('entries',[]),key=lambda e:e.get('logical_bytes',0),reverse=True)[:18]
                    maximum=max([e.get('logical_bytes',0) for e in entries] or [0])
                    rows.extend(['SIZE BARS / logical sizes, not allocated disk usage',''])
                    for entry in entries:
                        value=max(0,int(entry.get('logical_bytes',0)))
                        length=round(value/maximum*19) if maximum else 0
                        rows.append(f"{str(entry.get('name',''))[:19]:19} {'#'*length:<19} {readable_size(value)}")
                else:
                    rows.extend(['No completed scan for this folder yet.', 'Press S to scan; Esc navigates without stopping.'])
                return rows
            for i,item in enumerate(self.last_browser):
                prefix='▶' if i==self.content_cursor else ' '
                rows.append(f'{prefix} {item.name or str(item)}')
            if not self.last_browser:rows.append('(No accessible directories)')
            return rows
        if self.mode==1:
            rows=['SNAPSHOTS / Choose two scans of the same path','Enter: baseline / comparison   ↑↓: browse','']
            for i,s in enumerate(core.snapshots()):
                marker='▶' if i==self.content_cursor else ' '
                rows.append(f"{marker} #{s['id']}  {s['created'][:19]}  {s['root']}")
            if self.snapshot_anchor:rows.append(f'Baseline selected: #{self.snapshot_anchor}')
            if self.translation: rows+=['','LATEST COMPARISON:',self.translation['command']]
            return rows
        if self.mode==2:
            rows=['SAFE TEMP CLEANUP','R: re-scan candidates   X: preview-confirm deletion','Scope: direct regular files in user Temp, older than 7 days','Links / folders / changed / locked files are skipped','']
            if not self.report:return rows+['No preview available.']
            rows.append(f"{len(self.report['files'])} eligible files; {readable_size(self.report['bytes'])} logical bytes")
            rows.append('')
            for item in self.report['files'][:30]:
                rows.append(f"{readable_size(item['size']):>12}  {item['name']}")
            return rows
        if self.mode==3:
            return ['FILE OPERATIONS / SINGLE-FILE COPY', 'N: new verified copy (no overwrite)',
                    'Copies run in background, check SHA-256 and can be cancelled.',
                    'You can browse other pages while copy proceeds.',
                    '',self.message]
        if self.mode==4:
            return ['SYSTEM DOCTOR / READ-ONLY',f'Platform: {sys.platform}',
                    f'Python: {sys.version.split()[0]}',
                    f'Snapshot database: {core.DB_PATH}',
                    f'Event log folder: {self.jobs.log_dir}',
                    'Windows repair and DISM execution are not wired here yet.',
                    'This page never changes Windows settings.']
        if self.mode==5:
            rows=['COMMAND TRANSLATOR / PREVIEW ONLY',
                  'N: trusted recipe    O: old AI command preview',
                  'I: Ollama intent plan (1.5b)    P: offline intent demo',
                  'AI requires Ollama running and qwen2.5-coder:7b installed.',
                  'Generated commands are NEVER executed.',
                  '', 'EXAMPLES: free disk space / find largest files / clean temp',
                  '          list Ollama models / backup folder / checksum', '']
            job=self.jobs.current
            if self.result_mode=='command' and job and job.name=='Ollama translator' and job.state=='COMPLETED':
                self.translation=job.result
            elif self.result_mode=='command' and job and job.name=='Ollama translator' and job.state=='FAILED':
                rows.append('Local AI error: '+job.message)
            elif self.result_mode=='command' and job and job.name=='Ollama translator' and job.state in ('RUNNING','QUEUED','CANCELLING'):
                rows.append('Local AI is responding... watch status spinner / press C to cancel')
            if self.result_mode=='intent' and job and job.name=='Ollama intent classifier':
                if job.state=='COMPLETED':self.intent_plan=job.result
                elif job.state=='FAILED':rows.append('Intent classifier failed: '+job.message)
                elif job.state in ('RUNNING','QUEUED','CANCELLING'):
                    rows.append('Intent model is classifying... Esc back / C cancel')
            if self.translator_query:rows.extend(['REQUEST: '+self.translator_query,''])
            if self.intent_plan:
                plan=self.intent_plan
                rows += ['INTENT PLAN / NEVER EXECUTED',
                         'Operation: '+plan['intent'],
                         'Confidence: '+str(round(plan['confidence']*100))+'% / '+plan['provider'],
                         'Risk: '+plan['risk'],
                         'Ready for preview: '+str(plan['ready_for_preview']),
                         'Next: '+plan['next_step']]
                for k,v in plan['parameters'].items():
                    if v:rows.append(k+': '+v)
                for warning in plan['warnings']:rows.append('WARN: '+warning)
                for missing in plan['missing']:rows.append('MISSING: '+missing)
                rows.append('No command executed; AI did not get system access.')
            if self.result_mode=='command' and self.translation:
                rows.extend([self.translation['description'],f"RISK: {self.translation.get('risk','review')}"])
                for line in str(self.translation['command'] or '(no command found)').splitlines():
                    rows.extend(__import__('textwrap').wrap(line,75,break_long_words=False) or [''])
                rows.extend(['','NOTICE:',self.translation['notice']])
            return rows
        if self.mode==6:
            rows=['ARCADE / EXTERNAL OPEN-SOURCE GAMES',
                  '↑↓ choose game; Enter attempts to launch an installed binary',
                  'Always play as a standard Windows user, never Administrator.',
                  'Double-click PlayArcade.cmd for the non-elevated game menu.',
                  'Game folder: '+str(arcade.game_dir()),'']
            for i,g in enumerate(arcade.GAMES):
                installed=arcade.find_game(g)
                rows.extend([('> ' if self.game_cursor==i else '  ')+g.name+(' [INSTALLED]' if installed else ' [INSTALL FIRST]'),
                             '  '+g.project])
            rows.extend(['','No third-party game binaries are distributed with WinForge.',
                         'Download from the author and place binary in the game folder.'])
            return rows
        if self.mode==9:
            rows=['OLD VERSION MANAGER / CONFIRMED RECYCLING',
                  'R: refresh   ↑↓: select   Enter: preview/confirm',
                  'Only verified older sibling extraction folders can be recycled.',
                  'Never the running installation; NEVER a Git checkout.',
                  'OneDrive warning: recycled files may also be removed from cloud sync.',
                  '']
            if not self.old_versions:rows.append('No safe older sibling copies found.')
            for i,candidate in enumerate(self.old_versions):
                rows.extend([('> ' if i==self.content_cursor else '  ')+
                    f'v{candidate.version}   {candidate.path.name}   {readable_size(candidate.bytes_estimate)} logical',
                    '    '+str(candidate.path)])
            return rows
        if self.mode==10:
            job=self.jobs.current
            rows=['SELF-TEST / LOCAL CHECKS','R: run checks in background','Checks package structure, TUI rendering and core safety contracts.','']
            if job and job.name=='WinForge self-test':
                rows.append('Latest: '+job.state)
                if job.state=='COMPLETED':
                    for row in job.result:rows.append(('PASS ' if row['ok'] else 'FAIL ')+row['name']+': '+row['message'])
                if job.state=='FAILED':rows.append('ERROR: '+job.message)
            rows.extend(['','For full automated regression tests: double-click RunTests.cmd',
                         'Manual Windows/UAC/game smoke tests still required.'])
            return rows
        if self.mode==7:
            return ['HELP & CONTROLS','Tab: switch navigation/content   ↑↓: move',
                    'Enter: select   Esc: back (does NOT stop a job)',
                    'C / Ctrl+C: request cancellation at safe checkpoint',
                    'L: event logs   F1: help   Q: exit safely',
                    'Storage: D drives, G path, S scan, Backspace parent',
                    'Temp: R refresh, X preview deletion',
                    'Files: N copy, SHA-256 verified; no overwrite',
                    'Translation: N offline or O local Ollama (preview only)',
                    'A moving spinner means active; WAITING means idle.',
                    'Progress percent = completed top-level entries for scans.',
                    'A cancellable operation may require time to reach a checkpoint.',
                    f'Logs: {self.jobs.log_dir}',
                    'Version Manager: R discover, Enter to confirm Recycle Bin',
                    'Self-Test: R to run checks; RunTests.cmd for full suite',
                    'Arcade: use PlayArcade.cmd as standard user',
                    'Known limitation: source launcher requires Python 3.10+.']
        if self.mode==8:
            rows=[f'EVENT LOGS / {self.jobs.log_dir}','Recent audit events:','']
            rows += ['', 'OPERATOR PLANS / NAVIGATION (NOT EXECUTED)']
            for entry in self.activity.recent(8):
                rows.append(entry['timestamp'][11:19]+' '+entry['event']+': '+entry['operation'])
            rows += ['', 'LIVE TASK EVENTS']
            for e in self.jobs.events[-30:]:
                rows.append(f"[{e['timestamp'][-14:-6]}] {e['level']:7} {e['message']}")
            return rows
        return []

    def render(self, width: int=120, height: int=36, *, use_color=False, now:float|None=None) -> str:
        width=max(70,width);height=max(23,height)
        # 2 panes at all sizes; scroll content window to keep cursor visible.
        left_width=max(23,min(36,width//3))
        right_width=width-left_width-1
        logo='  CTRL + ALT + DEFEAT  '
        if width>=110 and height>=32:
            top=[color('═'*width,'purple',use_color)] + ascii_logo(width,use_color) + [
                 color(f'{logo}  v{VERSION}  •  by {AUTHOR}'.center(width),'yellow',use_color),
                 color('WHEN WINDOWS FIGHTS BACK, PRESS HARDER.'.center(width),'cyan',use_color),
                 color('─'*width,'gray',use_color)]
        else:
            top=[color('═'*width,'purple',use_color),
                 color(logo.center(width),'purple',use_color),
                 color(f'v{VERSION}  •  by {AUTHOR}'.center(width),'yellow',use_color),
                 color('WHEN WINDOWS FIGHTS BACK, PRESS HARDER.'.center(width),'cyan',use_color),
                 color('─'*width,'gray',use_color)]
        work_height=max(8,height-len(top)-7)
        nav=[]
        for i,(title,_) in enumerate(MENU):
            marker='▶' if self.menu_cursor==i and self.focus=='menu' else ('◆' if i==self.mode else ' ')
            nav.append(f' {marker} {i+1:02}. {title}')
        nav+=['','  Tab = switch pane','  Esc = back','  F1 = help','  L = logs','  C = cancel task']
        left=box('Modules' + (' [ACTIVE]' if self.focus=='menu' else ''),nav,left_width,work_height,'purple',use_color)
        content=self.content_lines()
        available=work_height-2
        if self.mode==0:
            start=max(0,min(self.content_cursor-10,max(0,len(content)-available)))
        elif self.mode==1:
            start=max(0,min(self.content_cursor,max(0,len(content)-available)))
        else:start=0
        right=box(self.current_module+(' [ACTIVE]' if self.focus=='content' else ''),content[start:],right_width,work_height,'cyan',use_color)
        lines=top + [left[i]+' '+right[i] for i in range(work_height)]
        job=self.jobs.current
        t=time.monotonic() if now is None else now
        spinner='-/|\\'[int(t*6)%4]
        if job and job.state in {'QUEUED','RUNNING','CANCELLING'}:
            status=f'{spinner} {job.state} #{job.id} {job.name}  elapsed {age(job.elapsed)}  files {job.files:,}'
            if job.percent is not None:
                bar_width=22;filled=int(job.percent/100*bar_width)
                status+=f'  [{"#"*filled}{"-"*(bar_width-filled)}] {job.percent:.0f}% entries'
            elif job.total is not None:status+='  [----------] counting entries'
            detail=f'Current: {job.current or job.target}'
        else:
            status='● WAITING FOR INPUT  |  no active operation'
            if job:status+=f'  | last #{job.id}: {job.state}'
            detail='Ready to browse or launch a task'
        if self.exit_when_idle and (not job or job.state not in {'QUEUED','RUNNING','CANCELLING'}):
            self.should_exit=True
        recent=self.jobs.events[-2:]
        log=recent[-1] if recent else None
        events=f"{log['timestamp'][11:19]} [{log['level']}] {log['message']}" if log else 'No audit events yet.'
        status_lines=[status,detail,events,self.message]
        if self.prompt: status_lines[-1]=f'{self.prompt.label}: {self.prompt.text}_'
        status_color = ('cyan' if job and job.state=='RUNNING' else
                        'yellow' if job and job.state in {'CANCELLING','QUEUED'} else
                        'green' if job and job.state=='COMPLETED' else
                        'red' if job and job.state=='FAILED' else 'purple')
        lines+=box('Operation status / live log',status_lines,width,6,status_color,use_color)
        # Fit terminal height if smaller than desired (and keep footer visible).
        footer=f' [{datetime.now().strftime("%H:%M:%S")}]  ↑↓ Move | Tab Focus | Enter Open | Esc Back | C Cancel | L Logs | Q Quit '
        lines.append(color(shorten(footer,width).ljust(width),'gray',use_color))
        return '\n'.join(lines[:height])


def _enable_windows_ansi():
    if os.name!='nt':return
    try:
        import ctypes
        kernel=ctypes.windll.kernel32
        h=kernel.GetStdHandle(-11)
        mode=ctypes.c_ulong()
        if kernel.GetConsoleMode(h,ctypes.byref(mode)):
            kernel.SetConsoleMode(h, mode.value | 0x0004)
    except (AttributeError, OSError):pass


def _read_keys():
    if os.name=='nt':
        import msvcrt
        keys=[]
        while msvcrt.kbhit():
            ch=msvcrt.getwch()
            if ch in ('\x00','\xe0'):
                special=msvcrt.getwch()
                keys.append({'H':'up','P':'down','K':'left','M':'right',';':'f1'}.get(special,'other'))
            else:keys.append({'\r':'enter','\x1b':'esc','\x08':'back','\t':'tab','\x03':'ctrl+c'}.get(ch,ch))
        return keys
    import select
    keys=[]
    while select.select([sys.stdin],[],[],0)[0]:
        ch=sys.stdin.read(1)
        if ch=='\x1b':
            if select.select([sys.stdin],[],[],0.003)[0]:
                n=sys.stdin.read(1)
                if n=='[' and select.select([sys.stdin],[],[],0.003)[0]:
                    keys.append({'A':'up','B':'down','C':'right','D':'left'}.get(sys.stdin.read(1),'esc'))
                else:keys.append('esc')
            else:keys.append('esc')
        else:keys.append({'\r':'enter','\n':'enter','\x7f':'back','\t':'tab','\x03':'ctrl+c'}.get(ch,ch))
    return keys


def run():
    """Full-screen alternating buffer; restores the original terminal on exit."""
    _enable_windows_ansi()
    controller=Controller()
    def loop():
        redraw=0.0
        while not controller.should_exit:
            for k in _read_keys():controller.handle_key(k)
            now=time.monotonic()
            if now>=redraw:
                size=shutil.get_terminal_size(fallback=(120,40))
                frame=controller.render(size.columns,max(23,size.lines),use_color=True,now=now)
                sys.stdout.write('\033[H'+frame+'\033[J')
                sys.stdout.flush()
                redraw=now+0.15
            time.sleep(0.035)
    import signal
    old_sigint=signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT,lambda *_: controller.action_cancel())
    try:
        if os.name!='nt':
            import termios,tty
            fd=sys.stdin.fileno();original=termios.tcgetattr(fd)
            tty.setcbreak(fd)
        sys.stdout.write('\033[?1049h\033[?25l\033[2J\033[H');sys.stdout.flush()
        loop()
    except KeyboardInterrupt:
        controller.action_cancel()
    finally:
        signal.signal(signal.SIGINT,old_sigint)
        sys.stdout.write('\033[?25h\033[?1049l'+RESET);sys.stdout.flush()
        if os.name!='nt':
            try:termios.tcsetattr(fd,termios.TCSADRAIN,original)
            except (OSError, NameError):pass

if __name__=='__main__':run()
