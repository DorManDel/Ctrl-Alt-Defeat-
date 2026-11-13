"""Offline, deterministic plain-English command suggestions. Never executes commands."""
from __future__ import annotations

RULES = [
    (('free space', 'disk space', 'storage'), 'Inspect disk free space', 'Get-PSDrive -PSProvider FileSystem'),
    (('running process', 'memory usage', 'ram usage'), 'Inspect top processes', 'Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15'),
    (('ollama', 'local models'), 'List Ollama models', 'ollama list'),
    (('steam download', 'steam cache'), 'Inspect Steam download queue files', 'Get-ChildItem "C:\\Program Files (x86)\\Steam\\steamapps\\downloading"'),
    (('windows update', 'update cache'), 'Open supported Windows Disk Cleanup', 'cleanmgr.exe'),
    (('network', 'ip address'), 'Inspect network adapters', 'Get-NetIPConfiguration'),
    (('system info', 'hardware'), 'Inspect system information', 'Get-ComputerInfo | Select-Object CsName,OsName,CsTotalPhysicalMemory'),
]


def suggest(query: str):
    q = query.casefold().strip()
    for terms, description, command in RULES:
        if any(t in q for t in terms):
            return {'matched': True, 'description': description, 'command': command,
                    'notice': 'Suggestion only. Review before executing; Ctrl+Alt+Defeat does not execute it.'}
    return {'matched': False, 'description': 'No trusted rule matched', 'command': None,
            'notice': 'No command was invented. Add a vetted recipe to the translator rules.'}
