import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import watcher


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.proc = self.root / 'proc'
        self.proc.mkdir()
        self.cwd = self.root / 'project'
        self.cwd.mkdir()
        self.rollout = self.root / 'rollout-current.jsonl'
        self.rollout.touch()
        self.other = self.root / 'rollout-other.jsonl'
        self.other.touch()
        self.ancestry = patch.object(watcher.notify, 'ancestors', side_effect=lambda pid: {pid: 'start'})
        self.ancestry.start()
        self.addCleanup(self.ancestry.stop)

    def client(self, pid, transcript=None, args=b'codex\0', cwd=None):
        process = self.proc / str(pid)
        process.mkdir()
        (process / 'comm').write_text('codex\n')
        (process / 'cmdline').write_bytes(args)
        (process / 'cwd').symlink_to(cwd or self.cwd)
        (process / 'fd').mkdir()
        (process / 'fd' / '0').symlink_to('/dev/pts/100')
        if transcript:
            (process / 'fd' / '3').symlink_to(transcript)
        return process

    def route(self):
        return watcher.cli_lineage(str(self.cwd), 'session', self.rollout, self.proc)

    def test_two_clients_same_project_select_exact_transcript(self):
        self.client(10, self.other)
        self.client(20, self.rollout)
        self.assertEqual(self.route(), {20: 'start'})

    def test_shared_daemon_is_not_the_terminal_client(self):
        self.client(10, self.rollout, b'codex\0app-server\0')
        self.client(20)
        self.client(30)
        self.assertEqual(self.route(), {})

    def test_ambiguous_transcript_owners_fail_closed(self):
        self.client(10, self.rollout)
        self.client(20, self.rollout)
        self.assertEqual(self.route(), {})

    def test_ambiguous_project_without_evidence(self):
        self.client(10)
        self.client(20)
        self.assertEqual(self.route(), {})

    def test_unique_project_preserves_existing_behavior(self):
        self.client(10)
        self.assertEqual(self.route(), {10: 'start'})

    def test_historical_resume_arguments_do_not_override_live_session(self):
        self.client(10, self.other, b'codex\0resume\0session\0')
        self.client(20, self.rollout)
        self.assertEqual(self.route(), {20: 'start'})

    def test_exact_session_works_after_cwd_changes(self):
        changed = self.root / 'changed'
        changed.mkdir()
        self.client(10, self.rollout, cwd=changed)
        self.assertEqual(self.route(), {10: 'start'})

    def test_unique_client_with_different_session_is_rejected(self):
        self.client(10, self.other)
        self.assertEqual(self.route(), {})

    def test_process_holding_multiple_transcripts_is_ambiguous(self):
        process = self.client(10, self.rollout)
        (process / 'fd' / '4').symlink_to(self.other)
        self.client(20)
        self.assertEqual(self.route(), {})


if __name__ == '__main__':
    unittest.main()
