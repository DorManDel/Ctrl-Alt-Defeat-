import tempfile
import unittest
from pathlib import Path
from ctrl_alt_defeat import core

class CoreTests(unittest.TestCase):
    def test_scan_and_transfer(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'sub').mkdir();(p/'sub'/'a.txt').write_text('hello')
            data=core.scan(p)
            self.assertEqual(data['entries'][0]['logical_bytes'],5)
            src=p/'sub'/'a.txt';dest=p/'copy.txt'
            preview=core.transfer(src,dest)
            self.assertFalse(preview['applied']);self.assertFalse(dest.exists())
            copied=core.transfer(src,dest,apply=True)
            self.assertTrue(copied['verified']);self.assertEqual(dest.read_text(),'hello')
            with self.assertRaises(FileExistsError):core.transfer(src,dest,apply=True)
    def test_compare(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'a.txt').write_text('a')
            a=core.scan(p);(p/'a.txt').write_text('aa');b=core.scan(p)
            old=core.DB_PATH
            try:
                core.DB_PATH=p/'test.db'
                one=core.save_snapshot(a);two=core.save_snapshot(b)
                diff=core.compare(one,two)
                self.assertEqual(diff['changes'][0]['delta'],1)
            finally:core.DB_PATH=old

if __name__=='__main__': unittest.main()
