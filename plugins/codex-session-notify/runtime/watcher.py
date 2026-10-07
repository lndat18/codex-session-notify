"""Follow real Codex task_complete records, including shared-daemon CLI sessions."""
import concurrent.futures
import json
import os
import sys
from pathlib import Path
import time

import notify

SESSIONS = notify.ROOT.parent / 'sessions'


def session_evidence(process, rollout):
    """Return exact live ownership evidence; never infer from a project name.

    An open transcript identifies current ownership. Launch arguments may be
    stale after /resume, so they are not used. None means no evidence.
    """
    transcripts = set()
    try:
        for fd in (process / 'fd').iterdir():
            try:
                target = Path(os.readlink(fd))
                if target.name.startswith('rollout-') and target.suffix == '.jsonl':
                    transcripts.add(target.resolve())
            except OSError:
                continue
    except OSError:
        pass
    if transcripts:
        return rollout.resolve() in transcripts and len(transcripts) == 1
    # Arguments are historical and cannot prove the current session after an
    # in-app /resume. They intentionally do not establish ownership by themselves.
    return None


def cli_lineage(cwd, sid=None, rollout=None, proc=Path('/proc')):
    """Prefer exact transcript ownership, retaining unique-cwd compatibility."""
    matches = []
    exact = []
    for path in proc.iterdir():
        if not path.name.isdigit():
            continue
        try:
            if (path / 'comm').read_text().strip() != 'codex':
                continue
            args = (path / 'cmdline').read_bytes().split(b'\0')
            if b'app-server' in args or b'exec' in args:
                continue
            if not os.readlink(path / 'fd' / '0').startswith('/dev/pts/'):
                continue
            pid = int(path.name)
            evidence = session_evidence(path, rollout) if rollout else None
            if evidence is True:
                exact.append(pid)
            if Path(os.readlink(path / 'cwd')).resolve() == Path(cwd).resolve():
                matches.append((pid, evidence))
        except (OSError, ValueError):
            continue
    if len(exact) == 1:
        return notify.ancestors(exact[0])
    if exact:
        return {}
    if len(matches) == 1 and matches[0][1] is not False:
        return notify.ancestors(matches[0][0])
    return {}


def completion(meta, record):
    source = meta.get('source')
    if (isinstance(source, dict) and 'subagent' in source) or source == 'subagent':
        return None
    payload = record.get('payload', {})
    if record.get('type') != 'event_msg' or payload.get('type') != 'task_complete':
        return None
    if not payload.get('turn_id') or not meta.get('id'):
        return None
    return {'type': 'agent-turn-complete', 'thread-id': meta['id'],
            'turn-id': payload['turn_id'], 'cwd': meta.get('cwd', ''), 'source': source,
            'last-assistant-message': payload.get('last_agent_message') or ''}


class Tail:
    def __init__(self, path, *, skip_existing):
        self.path = path
        self.meta = {}
        with path.open('rb') as stream:
            # session_meta is the first record in Codex rollout files.
            line = stream.readline()
            try:
                row = json.loads(line)
                if row.get('type') == 'session_meta':
                    self.meta = row.get('payload', {})
            except ValueError:
                pass
            stream.seek(0, 2) if skip_existing else stream.seek(0)
            self.offset = stream.tell()

    def poll(self):
        events = []
        size = self.path.stat().st_size
        if size == self.offset:
            return events
        with self.path.open('rb') as stream:
            if size < self.offset:
                self.offset = 0
            stream.seek(self.offset)
            while True:
                start = stream.tell()
                line = stream.readline()
                if not line or not line.endswith(b'\n'):
                    self.offset = start
                    break
                self.offset = stream.tell()
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get('type') == 'session_meta':
                    self.meta = row.get('payload', {})
                event = completion(self.meta, row)
                if event:
                    events.append(event)
        return events


def hooks_own_project(cwd, proc=Path('/proc')):
    """Managed CLI hooks deliver directly; avoid watcher winning dedup first."""
    owners = []
    for process in proc.iterdir():
        if not process.name.isdigit():
            continue
        try:
            if (process / 'comm').read_text().strip() != 'codex':
                continue
            args = (process / 'cmdline').read_bytes().split(b'\0')
            if b'app-server' in args or b'exec' in args:
                continue
            if not os.readlink(process / 'fd' / '0').startswith('/dev/pts/'):
                continue
            if Path(os.readlink(process / 'cwd')).resolve() != Path(cwd).resolve():
                continue
            expected = 'notify=' + json.dumps([sys.executable, str(notify.ROOT / 'notify.py')])
            owners.append(b'--no-daemon' in args and expected.encode() in args)
        except (OSError, ValueError):
            continue
    return bool(owners) and all(owners)


def send(event, rollout):
    try:
        if hooks_own_project(event['cwd']):
            return
        notify.deliver(event, lineage_provider=lambda: cli_lineage(event['cwd'], event['thread-id'], rollout), origin='watcher')
    except Exception as error:
        notify.log('watcher-error', session_id=event.get('thread-id'), detail=str(error))


def main():
    tails = {}
    # Never replay old replies when starting the background service.
    for path in SESSIONS.rglob('rollout-*.jsonl'):
        try:
            tails[path] = Tail(path, skip_existing=True)
        except OSError:
            pass
    notify.log('watcher-started', pid=os.getpid(), tracked_files=len(tails))
    next_discovery = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        while True:
            now = time.monotonic()
            if now >= next_discovery:
                for path in SESSIONS.rglob('rollout-*.jsonl'):
                    if path not in tails:
                        try:
                            tails[path] = Tail(path, skip_existing=False)
                        except OSError:
                            pass
                next_discovery = now + 2
            for path, tail in list(tails.items()):
                try:
                    for event in tail.poll():
                        pool.submit(send, event, path)
                except FileNotFoundError:
                    del tails[path]
                except OSError as error:
                    notify.log('watcher-read-error', detail=str(error))
            time.sleep(0.25)


if __name__ == '__main__':
    main()
