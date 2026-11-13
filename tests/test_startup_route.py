"""Regression: the actual CLI entry must launch the new dashboard."""
import argparse
import unittest
from unittest.mock import patch
from ctrl_alt_defeat import __main__ as cli


class StartupRouteTests(unittest.TestCase):
    def test_real_menu_dispatches_to_dashboard_not_legacy_tui(self):
        with patch('ctrl_alt_defeat.dashboard.run') as launch:
            cli.run(argparse.Namespace(command='menu'))
        launch.assert_called_once_with()

    def test_dashboard_version_and_author(self):
        from ctrl_alt_defeat import dashboard
        self.assertEqual(dashboard.VERSION, '0.5.2-dev')
        self.assertEqual(dashboard.AUTHOR, 'DorManDel')


if __name__ == '__main__':
    unittest.main()
