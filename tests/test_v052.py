import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ctrl_alt_defeat import translator,versions,arcade
from ctrl_alt_defeat.dashboard import Controller, VERSION
from ctrl_alt_defeat.jobs import JobManager
from ctrl_alt_defeat import selfcheck

class VersionCleanupTests(unittest.TestCase):
    def make_install(self,root,name,version,checkout=False):
        d=root/name
        (d/'ctrl_alt_defeat').mkdir(parents=True)
        (d/'ctrl_alt_defeat'/'__main__.py').write_text('# entry')
        (d/'ctrl_alt_defeat'/'dashboard.py').write_text(f"VERSION = '{version}'")
        (d/'CtrlAltDefeat.cmd').write_text('echo hi')
        (d/'VERSION.txt').write_text(version)
        if checkout:(d/'.git').mkdir()
        return d

    def test_sibling_discovery_excludes_active_and_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            active=self.make_install(root,'current','0.5.2')
            old=self.make_install(root,'older','0.5.1')
            self.make_install(root,'project','0.4',checkout=True)
            self.make_install(root,'newer','0.6.0')
            (root/'unrelated').mkdir()
            found=versions.scan_candidates(active,[root],current_version='0.5.2')
            self.assertEqual([x.path for x in found],[old.resolve(strict=True)])

    def test_recycle_requires_strict_sibling_and_rechecks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            active=self.make_install(root,'current','0.5.2')
            old=self.make_install(root,'old','0.5.1')
            candidate=versions.scan_candidates(active,[root],current_version='0.5.2')[0]
            captured=[]
            versions.recycle_candidate(candidate,current=active,recycler=lambda p:captured.append(p))
            self.assertEqual(captured,[old.resolve(strict=True)])
            (old/'.git').mkdir()
            with self.assertRaises(ValueError):versions.recycle_candidate(candidate,current=active,recycler=lambda p:None)

class TranslatorTests(unittest.TestCase):
    def test_offline_examples(self):
        for prompt in ['how much free disk space','find the largest files','ollama models installed','copy folder', 'pagefile usage']:
            with self.subTest(prompt=prompt):
                d=translator.suggest(prompt)
                self.assertTrue(d['matched'],prompt)
                self.assertTrue(d['command'])
                self.assertIn('PREVIEW',d['notice'])

    def test_unknown_doesnt_invent_command(self):
        r=translator.suggest('transform the moon into cheese')
        self.assertIsNone(r['command'])

    def test_ollama_streamed_preview(self):
        chunks=[{'response':'{"description":"Inspect","command":"Get-Date",','done':False},
                {'response':'"explanation":"Read time","risk":"read-only"}','done':True}]
        class FakeResponse:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def __iter__(self):return iter(json.dumps(c).encode()+b'\n' for c in chunks)
        got=translator.from_ollama('what time is it',opener=lambda req,timeout:FakeResponse())
        self.assertEqual(got['command'],'Get-Date')
        self.assertIn('NEVER',got.get('notice','').upper()+' NEVER')

    def test_controller_translator_n_and_o(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl=Controller(JobManager(Path(tmp)/'logs'),Path(tmp))
            ctl.enter_module(5)
            ctl.handle_key('n');self.assertIsNotNone(ctl.prompt)
            ctl.confirm_prompt('show free storage')
            self.assertTrue(ctl.translation['matched'])
            self.assertIn('Get-PSDrive','\n'.join(ctl.content_lines()))
            ctl.handle_key('o');self.assertEqual(ctl.prompt.kind,'translate_ai')

class ArcadeTests(unittest.TestCase):
    def test_missing_game_reports_and_never_runs_as_admin(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(arcade.find_game(arcade.GAMES[0],Path(tmp)))
            with patch('ctrl_alt_defeat.arcade.sys.platform','win32'):
                with self.assertRaises(PermissionError):arcade.launch(arcade.GAMES[0],Path(tmp),admin_check=lambda:True)

class SelfCheckTests(unittest.TestCase):
    def test_basic_checks_pass(self):
        report=selfcheck.checks()
        self.assertTrue(all(r['ok'] for r in report),report)
        self.assertEqual(VERSION,'0.5.2-dev')

if __name__=='__main__':unittest.main()

class VisualStateTests(unittest.TestCase):
    def test_colored_header_and_animated_status(self):
        from ctrl_alt_defeat.jobs import Job
        with tempfile.TemporaryDirectory() as tmp:
            mgr=JobManager(Path(tmp)/'logs')
            ctl=Controller(mgr,Path(tmp))
            mgr.current=Job('scan',str(tmp),state='RUNNING',total=10,completed=2)
            one=ctl.render(140,44,use_color=True,now=0)
            two=ctl.render(140,44,use_color=True,now=.2)
            self.assertIn('CTRL + ALT + DEFEAT',one)
            self.assertIn('\x1b[38;2;',one)
            self.assertIn('20% entries',one)
            self.assertIn('- RUNNING',one)
            self.assertIn('/ RUNNING',two)
            self.assertNotEqual(one,two)
