"""No-network contracts for the optional structured local intent planner."""
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request

from ctrl_alt_defeat import intent_router
from ctrl_alt_defeat.dashboard import Controller
from ctrl_alt_defeat.jobs import JobManager


class FakeStream:
    def __init__(self, content):
        self.lines = [json.dumps({'message': {'content':content[:11]}, 'done':False}).encode()+b'\n',
                      json.dumps({'message': {'content':content[11:]}, 'done':True}).encode()+b'\n']
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def __iter__(self):return iter(self.lines)


class IntentRouterTests(unittest.TestCase):
    def test_backup_json_plan_is_not_executed(self):
        want={'intent':'backup_files','summary':'Back up projects','source':'C:\\Projects',
              'destination':'D:\\Backup','target':None,'confidence':0.92}
        calls=[]
        def fake(request, timeout):
            self.assertIsInstance(request,Request)
            data=json.loads(request.data)
            self.assertEqual(data['model'],'qwen2.5-coder:1.5b')
            self.assertEqual(data['format']['additionalProperties'],False)
            self.assertFalse(any('tool' in msg for msg in data['messages']))
            calls.append(1)
            return FakeStream(json.dumps(want))
        plan=intent_router.from_ollama('Backup C:\\Projects to D:\\Backup', opener=fake)
        self.assertEqual(calls,[1])
        self.assertEqual(plan['intent'],'backup_files')
        self.assertTrue(plan['ready_for_preview'])
        self.assertFalse(plan['executed'])
        self.assertEqual(plan['parameters']['destination'],'D:\\Backup')

    def test_delete_request_is_not_executable(self):
        plan=intent_router.validate_plan({'intent':'delete_files','summary':'Delete folder',
              'target':'C:\\Data','source':None,'destination':None,'confidence':0.99})
        self.assertEqual(plan['risk'],'destructive')
        self.assertFalse(plan['executed'])
        self.assertTrue(plan['warnings'])
        root=intent_router.validate_plan({'intent':'delete_files','summary':'Delete drive',
              'target':'C:\\','source':None,'destination':None,'confidence':0.99})
        self.assertTrue(root['blocked'])
        self.assertFalse(root['ready_for_preview'])

    def test_invalid_and_unknown_operations_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            intent_router.validate_plan({'intent':'run_shell','summary':'bad',
              'confidence':1})
        with self.assertRaisesRegex(ValueError, 'confidence'):
            intent_router.validate_plan({'intent':'scan_storage','summary':'bad',
              'confidence':9})

    def test_no_paths_fabricated_by_offline_demo(self):
        plan=intent_router.offline_demo('בבקשה תעשה גיבוי')
        self.assertEqual(plan['intent'],'backup_files')
        self.assertEqual(plan['missing'],['source','destination'])
        self.assertFalse(plan['ready_for_preview'])
        self.assertFalse(plan['executed'])
        self.assertEqual(plan['provider'],'offline-keywords')

    def test_hebrew_maintenance_requests_and_negation(self):
        cases=[('גבה את הפרויקט', 'backup_files'),
               ('כמה מקום יש לי בכונן', 'scan_storage'),
               ('מחק תיקיית קבצים', 'delete_files'),
               ('אל תמחק כלום', 'unknown')]
        for query, expected in cases:
            with self.subTest(query=query):
                plan=intent_router.offline_demo(query)
                self.assertEqual(plan['intent'], expected)
                self.assertFalse(plan['executed'])

    def test_cancel_prevents_model_plan(self):
        event=threading.Event();event.set()
        response={'intent':'scan_storage','summary':'scan','source':None,
                  'destination':None,'target':None,'confidence':0.9}
        with self.assertRaises(InterruptedError):
            intent_router.from_ollama('Scan disk',cancel_event=event,
                                      opener=lambda request,timeout:FakeStream(json.dumps(response)))

    def test_ui_routes_intent_request_without_execution(self):
        with tempfile.TemporaryDirectory() as d:
            ctl=Controller(JobManager(Path(d)/'logs'),Path(d))
            ctl.enter_module(5);ctl.handle_key('p')
            self.assertEqual(ctl.prompt.kind,'intent_offline')
            ctl.confirm_prompt('please clean temp files')
            self.assertEqual(ctl.intent_plan['intent'],'clean_temp')
            self.assertIn('NEVER EXECUTED','\n'.join(ctl.content_lines()))
            ctl.handle_key('i');self.assertEqual(ctl.prompt.kind,'intent_ollama')


if __name__ == '__main__':unittest.main()
