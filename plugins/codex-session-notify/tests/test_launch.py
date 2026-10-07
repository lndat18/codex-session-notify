import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import launch
import watcher
import notify


class LaunchTests(unittest.TestCase):
    def test_resume_and_paths_are_preserved_without_shell(self):
        args = ['resume', 'session-123', '-C', '/tmp/a project', 'literal $(id)']
        result = launch.command(args, '/bin/codex')
        self.assertEqual(result[:3], ['/bin/codex', '--no-daemon', '-c'])
        self.assertEqual(json.loads(result[3].split('=', 1)[1]),
                         [sys.executable, str(launch.ROOT / 'notify.py')])
        self.assertEqual(result[4:], args)

    def test_remote_is_rejected(self):
        for args in [['--remote', 'unix://test'], ['--remote=unix://test']]:
            with self.assertRaises(ValueError):
                launch.command(args, '/bin/codex')

    def test_conflicting_hook_is_rejected(self):
        for args in [['-c', 'notify=[]'], ['--config=notify=[]'], ['-cnotify=[]']]:
            with self.assertRaises(ValueError):
                launch.command(args, '/bin/codex')

    def test_unrelated_config_is_preserved(self):
        self.assertEqual(launch.command(['-c', 'model="test"'], '/bin/codex')[-2:],
                         ['-c', 'model="test"'])

    def test_managed_hook_prevents_watcher_receipt_race(self):
        with patch.object(watcher, 'hooks_own_project', return_value=True), \
             patch.object(notify, 'deliver') as deliver:
            watcher.send({'cwd': '/project'}, Path('/transcript'))
            deliver.assert_not_called()

    def test_hook_ancestry_selects_each_terminal_in_same_project(self):
        records = [dict(timestamp=100, terminalPid=10, terminalStart='a'),
                   dict(timestamp=100, terminalPid=20, terminalStart='b')]
        self.assertEqual(notify.active_record(records, {30: 'c', 10: 'a'}, 101)['terminalPid'], 10)
        self.assertEqual(notify.active_record(records, {40: 'd', 20: 'b'}, 101)['terminalPid'], 20)


if __name__ == '__main__':
    unittest.main()
