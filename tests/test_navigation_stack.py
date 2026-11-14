"""State-restoration and live size-visualization regression contracts."""
import tempfile
import unittest
from pathlib import Path
from ctrl_alt_defeat.navigation import Location, NavigationStack
from ctrl_alt_defeat.dashboard import Controller
from ctrl_alt_defeat.jobs import JobManager, Job

class NavigationTests(unittest.TestCase):
    def test_lifo_deduplicated_and_bounded(self):
        h=NavigationStack(limit=2)
        a=Location(0,'content',Path('C:/'),False,0)
        b=Location(1,'content',Path('C:/'),False,0)
        c=Location(2,'menu',Path('C:/'),False,0)
        h.remember(a);h.remember(a);h.remember(b);h.remember(c)
        self.assertEqual(h.depth,2)
        self.assertEqual(h.back(),c)
        self.assertEqual(h.back(),b)
        self.assertIsNone(h.back())

    def test_escape_restores_screen_and_keeps_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            m=JobManager(root/'logs');ctl=Controller(m,root)
            job=Job('scan',str(root),state='RUNNING')
            m.current=job
            ctl.enter_module(5)
            self.assertEqual(ctl.mode,5)
            ctl.action_back()
            self.assertEqual(ctl.mode,0)
            self.assertEqual(ctl.focus,'menu')
            self.assertIs(m.current,job)
            self.assertEqual(job.state,'RUNNING')

    def test_folder_back_restores_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sub').mkdir()
            ctl=Controller(JobManager(root/'logs'),root)
            ctl.focus='content';ctl.refresh_content()
            idx=[p.name for p in ctl.last_browser].index('sub')
            ctl.content_cursor=idx
            ctl.handle_key('enter')
            self.assertEqual(ctl.path,root/'sub')
            ctl.handle_key('esc')
            self.assertEqual(ctl.path,root)
            self.assertEqual(ctl.content_cursor,idx)

    def test_storage_bars_are_from_actual_snapshot_data_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);mgr=JobManager(root/'logs')
            ctl=Controller(mgr,root);ctl.focus='content'
            ctl.handle_key('v')
            self.assertIn('No completed scan', '\n'.join(ctl.content_lines()))
            mgr.current=Job('Storage scan',str(root),state='COMPLETED',result={
                'root':str(root),'entries':[{'name':'alpha','logical_bytes':1024},
                                                {'name':'beta','logical_bytes':512}]})
            view='\n'.join(ctl.content_lines())
            self.assertIn('SIZE BARS',view)
            self.assertIn('alpha',view)
            self.assertIn('beta',view)
            self.assertIn('logical',view.lower())

if __name__ == '__main__':unittest.main()
