import tempfile
import threading
import time
import unittest
from pathlib import Path
from ctrl_alt_defeat import core
from ctrl_alt_defeat.dashboard import Controller
from ctrl_alt_defeat.jobs import JobManager, Job, Cancelled


class ProgressContracts(unittest.TestCase):
    def test_actual_top_level_progress_and_file_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'folder').mkdir()
            (root/'folder'/'a.txt').write_text('hello')
            (root/'single.txt').write_text('world')
            totals=[];seen_files=[];done=[]
            def progress(**kw):
                if 'total' in kw:totals.append(kw['total'])
                if 'files' in kw:seen_files.append(kw['files'])
                if 'completed' in kw:done.append(kw['completed'])
            snapshot=core.scan(root,progress=progress)
            self.assertEqual(totals,[2])
            self.assertEqual(sum(seen_files),2)
            self.assertEqual(sum(done),2)
            self.assertEqual(sum(e['files'] for e in snapshot['entries']),2)

    def test_cancellation_between_files_and_no_symlink_recursion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);child=root/'child';child.mkdir()
            for i in range(10):(child/f'{i}.txt').write_text('data')
            stop=threading.Event()
            def progress(**kw):
                if kw.get('files',0)>0:stop.set()
            with self.assertRaises(Cancelled):core.scan(root,progress=progress,cancel_event=stop)
            link=root/'link'
            try:
                link.symlink_to(child,target_is_directory=True)
            except (OSError,NotImplementedError):return
            self.assertTrue(core.is_linklike(link))
            self.assertEqual(len(core.scan(root)['entries']),1)

    def test_running_status_and_safe_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr=JobManager(Path(tmp)/'log')
            ctrl=Controller(mgr,Path(tmp))
            fake=Job('unit scan','test')
            fake.state='RUNNING';fake.total=4;fake.completed=1;fake.files=3;fake.current='test.bin'
            mgr.current=fake
            frame=ctrl.render(120,36,use_color=False,now=5.0)
            self.assertIn('RUNNING',frame)
            self.assertIn('25% entries',frame)
            self.assertIn('test.bin',frame)
            self.assertIn('files 3',frame)
            ctrl.request_exit()
            self.assertFalse(ctrl.should_exit)
            self.assertTrue(fake.cancel_event.is_set())
            fake.state='CANCELLED'
            ctrl.render(120,36,use_color=False)
            self.assertTrue(ctrl.should_exit)

    def test_no_copy_until_exact_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'s';dst=root/'d';src.write_bytes(b'content')
            c=Controller(JobManager(root/'logs'),root);c.enter_module(3)
            c.handle_key('n')
            for ch in str(src):c.handle_key(ch)
            c.handle_key('enter')
            for ch in str(dst):c.handle_key(ch)
            c.handle_key('enter')
            self.assertEqual(c.prompt.kind,'copy_approve')
            c.handle_key('esc')
            self.assertFalse(dst.exists())

if __name__=='__main__':unittest.main()
