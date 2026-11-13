"""Fast non-destructive verification callable from the running TUI."""
from pathlib import Path
from . import dashboard, translator, versions

def checks():
    root=Path(__file__).resolve().parents[1]
    result=[]
    def record(name, ok, message=''):
        result.append({'name':name,'ok':bool(ok),'message':str(message)})
    record('Launch files exist',(root/'CtrlAltDefeat.cmd').is_file() and (root/'launcher.ps1').is_file(),'checked command + launcher')
    record('Package entry exists',(root/'ctrl_alt_defeat'/'__main__.py').is_file(),'checked Python package')
    record('Version matches', (root/'VERSION.txt').read_text().strip()==dashboard.VERSION.split('-')[0],dashboard.VERSION)
    record('Correct ASCII brand', 'CTRL + ALT + DEFEAT' in dashboard.Controller().render(120,40), 'header has canonical title')
    record('Offline translator',translator.suggest('how much free space on C')['matched'],'known intent resolved')
    record('Version manager safeguards', versions._version(root) is not None, 'source is verifiable')
    return result

def run_checks(job,mgr):
    report=[]
    for idx,fn in enumerate((lambda:checks(),)):
        mgr.checkpoint(job,current='Verifying module contracts')
        report.extend(fn())
    for row in report:
        mgr.log('INFO' if row['ok'] else 'ERROR',f"{row['name']}: {row['message']}",job)
    if not all(item['ok'] for item in report):raise RuntimeError('One or more self-checks failed')
    mgr.checkpoint(job,completed=1,total=1)
    return report
