"""Headless contract tests for responsive UI, cancellation, and audited jobs."""
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from ctrl_alt_defeat.dashboard import Controller, box, MENU
from ctrl_alt_defeat.jobs import JobManager, Job, Cancelled, scan_operation, copy_operation


class DashboardTests(unittest.TestCase):
    def test_brand_author_two_panes_and_status(self):
        with tempfile.TemporaryDirectory() as t:
            c=Controller(jobs=JobManager(Path(t)/'logs'), path=Path(t))
            for size in [(80,24),(120,40)]:
                out=c.render(*size,use_color=False,now=0)
                self.assertIn('CTRL + ALT + DEFEAT',out)
                self.assertIn('by DorManDel',out)
                self.assertIn('MODULES',out.upper())
                self.assertIn('STORAGE DETECTIVE',out.upper())
                self.assertIn('WAITING FOR INPUT',out)
                self.assertIn('↑↓',out)
                self.assertNotIn('Ctrl H Defeat',out)

    def test_back_and_prompt_cancel_without_exiting(self):
        with tempfile.TemporaryDirectory() as t:
            c=Controller(JobManager(Path(t)/'logs'),Path(t))
            c.focus='content'
            c.handle_key('g')
            self.assertIsNotNone(c.prompt)
            c.handle_key('a');c.handle_key('back')
            c.handle_key('esc')
            self.assertIsNone(c.prompt)
            self.assertFalse(c.should_exit)
            c.handle_key('esc')
            self.assertEqual(c.focus,'menu')

    def test_navigate_folders_and_scanning_in_background(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'child').mkdir();(root/'child'/'hello.txt').write_text('test')
            jobs=JobManager(root/'logs');c=Controller(jobs,root)
            c.focus='content';c.handle_key('s')
            self.assertIsNotNone(jobs.current)
            c.handle_key('l')
            self.assertEqual(c.current_module,'Event Logs')
            c.handle_key('esc')
            self.assertFalse(c.should_exit)
            jobs.current.thread.join(timeout=4)
            self.assertEqual(jobs.current.state,'COMPLETED')
            self.assertTrue(any(e['name']=='child' for e in jobs.current.result['entries']))
            self.assertIn('Snapshot', '\n'.join(e['message'] for e in jobs.events))

    def test_snapshot_scan_can_be_cancelled_at_checkpoint(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); mgr=JobManager(root/'logs'); gate=threading.Event()
            def operation(job, mgr):
                gate.set()
                while True:
                    mgr.checkpoint(job,current='big_folder',files=1)
                    time.sleep(.005)
            job=mgr.start('long scan',str(root),operation)
            self.assertTrue(gate.wait(2))
            self.assertTrue(mgr.cancel())
            job.thread.join(timeout=3)
            self.assertEqual(job.state,'CANCELLED')
            logs=list((root/'logs').glob('*.jsonl'))
            self.assertTrue(logs)
            events=[json.loads(line) for line in logs[0].read_text().splitlines()]
            self.assertTrue(any(x['level']=='WARN' and 'Cancellation' in x['message'] for x in events))

    def test_cancellable_non_overwriting_file_copy(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); src=root/'source.bin';dst=root/'copy.bin'
            src.write_bytes(b'abcd'*1024)
            mgr=JobManager(root/'logs')
            j=mgr.start('copy',str(src),copy_operation(src,dst,chunk_size=1024))
            j.thread.join(timeout=4)
            self.assertEqual(j.state,'COMPLETED')
            self.assertEqual(src.read_bytes(),dst.read_bytes())
            j2=mgr.start('copy again',str(src),copy_operation(src,dst))
            j2.thread.join(timeout=4)
            self.assertEqual(j2.state,'FAILED')
            self.assertEqual(dst.read_bytes(),src.read_bytes())

    def test_already_cancelled_copy_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);s=root/'a';d=root/'b';s.write_bytes(b'x'*1024)
            mgr=JobManager(root/'logs');j=Job('copy',str(s));j.cancel_event.set()
            with self.assertRaises(Cancelled):copy_operation(s,d)(j,mgr)
            self.assertFalse(d.exists())

    def test_log_has_timestamp_and_activity_state(self):
        with tempfile.TemporaryDirectory() as t:
            mgr=JobManager(Path(t)/'logs');event=mgr.log('INFO','hello world')
            self.assertIn('+',event['timestamp'])
            self.assertEqual(event['message'],'hello world')
            self.assertTrue(list((Path(t)/'logs').glob('*.jsonl')))

    def test_menu_module_navigation_and_help(self):
        with tempfile.TemporaryDirectory() as t:
            c=Controller(JobManager(Path(t)/'logs'),Path(t))
            c.handle_key('down');c.handle_key('enter')
            self.assertEqual(c.mode,1)
            c.handle_key('f1')
            self.assertEqual(c.current_module,'Help & Controls')
            self.assertIn('cancellation',c.render(100,35).lower())

if __name__=='__main__':unittest.main()
