import importlib.util
from pathlib import Path
import subprocess
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('notify_installer', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
sys.path.insert(0, str(ROOT / 'runtime'))
import launch

class ShellTests(unittest.TestCase):
    def test_idempotent_and_removable(self):
        original = 'export EXAMPLE=ok\n'
        result = installer.shell_config(original, 'bash')
        self.assertEqual(installer.shell_config(result, 'bash'), result)
        self.assertEqual(installer.shell_config(result, 'bash', True), original)
        subprocess.run(['bash', '-n'], input=result, text=True, check=True)

    def test_preserve_existing_function(self):
        with self.assertRaises(ValueError):
            installer.shell_config('codex() { echo custom; }\n', 'bash')

    def test_admin_passthrough(self):
        for args in [['plugin', 'list'], ['exec', 'test'], ['-c', 'model="x"', 'login'],
                     ['--remote=unix://test'], ['--help'], ['-c', 'notify=[]']]:
            self.assertEqual(launch.command(args, '/bin/codex', True), ['/bin/codex', *args])

    def test_normal_and_resume_use_automatic_routing(self):
        for args in [[], ['resume'], ['resume', 'id'], ['-m', 'model', 'my prompt']]:
            self.assertIn('--no-daemon', launch.command(args, '/bin/codex', True))
