"""The planning inventory must not silently become an executable AI tool registry."""
import json
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / 'planning' / 'capability_catalog.json'


class PlanningCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding='utf-8'))

    def test_is_design_only_not_executable(self):
        self.assertTrue(self.catalog['planning_only'])
        self.assertEqual(self.catalog['schema_version'], 1)
        for entry in self.catalog['entries']:
            self.assertFalse(entry['executable_by_ai'], entry['id'])
            self.assertTrue(entry['ai_execution_requires_explicit_approval'], entry['id'])

    def test_identifiers_unique_and_fields_present(self):
        entries = self.catalog['entries']
        self.assertGreaterEqual(len(entries), 35)
        self.assertEqual(len(entries), len({item['id'] for item in entries}))
        for entry in entries:
            with self.subTest(id=entry['id']):
                self.assertRegex(entry['id'], r'^[a-z_]+\.[a-z_]+$')
                self.assertIn(entry['status'], self.catalog['status_values'])
                self.assertIn(entry['risk'], self.catalog['risk_values'])
                self.assertIn(entry['priority'], {'P0','P1','P2','P3'})
                self.assertTrue(entry['name'] and entry['category'] and entry['planned_adapter'])
                self.assertIsInstance(entry['parameters'], list)
                self.assertIn(entry['undo_policy'], {'none','adapter-specific','restore-supported'})
                self.assertNotIn('command', entry)
                self.assertNotIn('argv', entry)

    def test_privileged_and_destructive_capabilities_remain_non_executable(self):
        sensitive = [x for x in self.catalog['entries'] if x['risk'] in {'destructive','privileged'}]
        self.assertGreaterEqual(len(sensitive), 5)
        self.assertTrue(all(not x['executable_by_ai'] for x in sensitive))


if __name__ == '__main__':
    unittest.main()
