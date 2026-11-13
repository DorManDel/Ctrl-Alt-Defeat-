import os
import tempfile
import time
import unittest
from pathlib import Path
from ctrl_alt_defeat import cleanup

class TempCleanupTests(unittest.TestCase):
    def test_only_old_regular_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            old=root/'old.tmp';old.write_bytes(b'1234')
            recent=root/'new.tmp';recent.write_bytes(b'fresh')
            stamp=time.time()-10*86400
            os.utime(old,(stamp,stamp))
            preview=cleanup.preview_user_temp(days=7,base=root)
            self.assertEqual([f['name'] for f in preview['files']],['old.tmp'])
            result=cleanup.delete_user_temp(preview)
            self.assertEqual(result['deleted'],1)
            self.assertFalse(old.exists())
            self.assertTrue(recent.exists())
    def test_modified_after_preview_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/'old.tmp';f.write_bytes(b'old')
            stamp=time.time()-10*86400;os.utime(f,(stamp,stamp))
            preview=cleanup.preview_user_temp(base=root)
            f.write_bytes(b'new content')
            result=cleanup.delete_user_temp(preview)
            self.assertEqual(result['skipped'],1)
            self.assertTrue(f.exists())

if __name__=='__main__': unittest.main()
