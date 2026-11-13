import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from ctrl_alt_defeat import capacity, translator

class ExtensionTests(unittest.TestCase):
    def test_preview_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            # Simulate an external volume: Windows Temp normally lives on C:.
            # Do not weaken the application's real system-drive safety guard.
            with patch.object(capacity, '_is_system_drive', return_value=False):
                r=capacity.probe(Path(d),1,reserve_mib=5120)
            self.assertFalse(r['applied'])
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_small_write_verify_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            # Only the 1 MiB throwaway test file is written in this sandbox.
            with patch.object(capacity, '_is_system_drive', return_value=False):
                r=capacity.probe(Path(d),1,mode='random',apply=True,cleanup=True,reserve_mib=5120)
            self.assertEqual(r['verified_mib'],1)
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_system_drive_safety_guard_remains_active(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(capacity, '_is_system_drive', return_value=True):
                with self.assertRaisesRegex(ValueError, 'system drive'):
                    capacity.probe(Path(d), 1, apply=True)
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_refuse_delete_foreign_file(self):
        with tempfile.TemporaryDirectory() as d:
            t=Path(d)/'.winforge-capacity-test';t.mkdir()
            (t/'important.txt').write_text('hello')
            with self.assertRaises(ValueError):capacity.cleanup_test(t)
            self.assertTrue((t/'important.txt').exists())
    def test_translator_no_execution(self):
        self.assertFalse(translator.suggest('delete everything immediately')['matched'])
        self.assertIn('Get-PSDrive',translator.suggest('check free space')['command'])

if __name__=='__main__':unittest.main()
