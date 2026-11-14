"""Audit journaling does not imply AI execution or save raw request paths."""
import tempfile
import unittest
from pathlib import Path
from ctrl_alt_defeat.activity import ActivityJournal
from ctrl_alt_defeat.dashboard import Controller
from ctrl_alt_defeat.jobs import JobManager


class ActivityTests(unittest.TestCase):
    def test_plans_are_append_only_with_no_raw_paths_or_exec_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'activity.jsonl'
            journal=ActivityJournal(p)
            journal.record_plan({'intent':'backup_files','risk':'write',
                'provider':'offline-keywords','parameters':{'source':'C:\\Private\\Secrets'}})
            journal.record('navigation', operation='Storage Detective')
            history=journal.recent()
            self.assertEqual(len(history),2)
            self.assertFalse(history[0]['executed'])
            self.assertNotIn('Secrets',p.read_text(encoding='utf-8'))
            self.assertTrue(history[0]['timestamp'])

    def test_operator_prompt_is_not_logged_as_raw_task_target(self):
        import unittest.mock
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ctl=Controller(JobManager(root/'logs'),root)
            ctl.enter_module(5)
            ctl.handle_key('i')
            request='Backup my private FOLDERKEY_123'
            sample={'intent':'backup_files','summary':request,
                    'source':None,'destination':None,'target':None,'confidence':0.8}
            from ctrl_alt_defeat import intent_router
            with unittest.mock.patch.object(intent_router,'from_ollama',
                       side_effect=lambda *args, **kwargs:intent_router.validate_plan(sample)):
                ctl.confirm_prompt(request)
                ctl.jobs.current.thread.join(timeout=3)
            logfile='\n'.join(x.read_text() for x in (root/'logs').glob('*.jsonl'))
            self.assertNotIn('FOLDERKEY_123',logfile)
            self.assertIn('local request withheld',logfile)

    def test_cannot_claim_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal=ActivityJournal(Path(tmp)/'audit.jsonl')
            with self.assertRaises(ValueError):journal.record('plan_prepared',executed=True)
            with self.assertRaises(ValueError):journal.record('unknown-event')

    def test_ui_writes_plan_and_navigation_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ctl=Controller(JobManager(root/'logs'),root)
            ctl.enter_module(5)
            ctl.handle_key('p')
            ctl.confirm_prompt('please backup my files')
            entries=ctl.activity.recent()
            self.assertEqual([x['event'] for x in entries],['navigation','plan_prepared'])
            self.assertFalse(entries[-1]['executed'])
            self.assertEqual(entries[-1]['operation'],'backup_files')
