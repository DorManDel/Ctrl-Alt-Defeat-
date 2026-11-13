"""Headless regression tests for Windows console/tab titles."""
import io
import unittest
from ctrl_alt_defeat.terminal_title import TerminalTitle, make_title


class TtyStream(io.StringIO):
    def isatty(self):
        return True


class FakeKernel:
    def __init__(self):
        self.titles = []

    def GetConsoleTitleW(self, buffer, length):
        buffer.value = 'Administrator: Windows PowerShell'
        return len(buffer.value)

    def SetConsoleTitleW(self, title):
        self.titles.append(title)
        return 1


class TerminalTitleTests(unittest.TestCase):
    def test_title_contains_brand_state_version(self):
        self.assertEqual(make_title('RUNNING', 'Storage scan'),
                         'Ctrl+Alt+Defeat [RUNNING] Storage scan | v0.5.2-dev')

    def test_untrusted_control_sequences_are_removed(self):
        title = make_title('RUNNING', 'hi\x1b]0;Bad\x07\nworld')
        self.assertNotIn('\x1b', title)
        self.assertNotIn('\x07', title)
        self.assertNotIn('\n', title)
        self.assertLess(len(title), 100)

    def test_ready_title_hides_paths(self):
        self.assertNotIn('Users', make_title('READY', r'C:\Users\Private'))

    def test_windows_title_changes_only_on_state_change(self):
        stream = TtyStream()
        kernel = FakeKernel()
        title = TerminalTitle(stream=stream, windows=True, kernel=kernel)
        title.update('READY')
        title.update('READY')
        title.update('RUNNING', 'Storage scan')
        title.restore()
        self.assertEqual(len(kernel.titles), 3)
        self.assertEqual(kernel.titles[-1], 'Administrator: Windows PowerShell')
        self.assertIn('\x1b]0;Ctrl+Alt+Defeat [READY]', stream.getvalue())

    def test_redirected_output_contains_no_title_escapes(self):
        stream = io.StringIO()
        title = TerminalTitle(stream=stream, windows=False)
        title.update('FAILED')
        self.assertEqual(stream.getvalue(), '')

    def test_terminal_emulator_mode(self):
        stream = TtyStream()
        title = TerminalTitle(stream=stream, windows=False)
        title.update('QUEUED', 'Task')
        self.assertIn('Ctrl+Alt+Defeat [QUEUED] Task', stream.getvalue())


if __name__ == '__main__':
    unittest.main()
