"""Codex notify command: Windows toast with session title and terminal-aware focus."""
import base64
import datetime
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
PS = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'


def trim(text, limit):
    text = re.sub(r'\s+', ' ', str(text)).strip()
    return text if len(text) <= limit else text[:limit-1].rstrip() + '…'


def clean(text):
    text = re.sub(r'```.*?```', ' [code] ', text, flags=re.S)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return re.sub(r'[`*_#>|]', '', text)


def session_title(sid, index=None):
    index = ROOT.parent / 'session_index.jsonl' if index is None else Path(index)
    title = ''
    try:
        with index.open(encoding='utf-8') as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get('id') == sid:
                    title = row.get('thread_name') or title
    except (OSError, TypeError):
        pass
    return title


def ancestors(pid=None):
    result = {}
    pid = os.getpid() if pid is None else pid
    for _ in range(64):
        try:
            stat = Path(f'/proc/{pid}/stat').read_text()
            fields = stat[stat.rfind(')') + 2:].split()
            result[pid] = fields[19]
            parent = int(fields[1])
        except (OSError, ValueError, IndexError):
            break
        if parent <= 1 or parent == pid:
            break
        pid = parent
    return result


def watching(records, lineage, now):
    # Fail open: missing, stale, or conflicting window state must not lose a notification.
    focused = [r for r in records if r.get('focused') is True
               and 0 <= now - r.get('timestamp', 0) < 3]
    if len(focused) != 1:
        return False
    row = focused[0]
    pid = row.get('terminalPid')
    return pid in lineage and row.get('terminalStart') == lineage[pid]


def focus_records():
    rows = []
    for path in (ROOT / 'focus').glob('*.json'):
        try:
            row = json.loads(path.read_text())
            if isinstance(row, dict):
                rows.append(row)
        except (OSError, ValueError):
            pass
    merged = {}
    for row in rows:
        key = (tuple(row.get('workspace', [])), row.get('terminalPid'), row.get('terminalStart'))
        if key not in merged or row.get('timestamp', 0) > merged[key].get('timestamp', 0):
            merged[key] = row
    return list(merged.values())


def log(status, **fields):
    ROOT.mkdir(parents=True, exist_ok=True)
    with (ROOT / 'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'time': datetime.datetime.now().isoformat(),
                                 'status': status, **fields}, ensure_ascii=False) + '\n')


def claim_turn(sid, turn_id):
    if not turn_id:
        return True
    ROOT.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(ROOT / 'receipts.sqlite', timeout=10) as db:
        db.execute('CREATE TABLE IF NOT EXISTS receipts (session TEXT, turn TEXT, PRIMARY KEY(session,turn))')
        try:
            db.execute('INSERT INTO receipts VALUES (?,?)', (sid, turn_id))
            return True
        except sqlite3.IntegrityError:
            return False


def release_turn(sid, turn_id):
    if turn_id:
        with sqlite3.connect(ROOT / 'receipts.sqlite', timeout=10) as db:
            db.execute('DELETE FROM receipts WHERE session=? AND turn=?', (sid, turn_id))


def main():
    test = '--test' in sys.argv
    if test:
        data = {'thread-id': 'test', 'cwd': str(Path.cwd()),
                'last-assistant-message': 'Thông báo Codex: tiếng báo, icon và nội dung tiếng Việt. ' * 6}
    else:
        if len(sys.argv) < 2:
            raise ValueError('Codex notify expects one JSON argument. For a manual test use --test.')
        data = json.loads(sys.argv[1])
        if data.get('type') != 'agent-turn-complete':
            return
    deliver(data, test=test)


def deliver(data, *, test=False, lineage=None, origin='notify'):
    sid = str(data.get('thread-id') or 'unknown')
    turn_id = data.get('turn-id')
    records = focus_records()
    lineage = ancestors() if lineage is None else lineage
    candidate = not test and watching(records, lineage, time.time())
    selected = next((r for r in records if r.get('focused') is True), {}) if candidate else {}
    title = session_title(sid)
    project = Path(data.get('cwd') or '.').name
    payload = {
        'session_id': sid,
        'title': trim(title or f'{project} · {sid[:8]}', 64),
        'body': trim(clean(data.get('last-assistant-message') or 'Đã trả lời xong.'), 180),
        'project': trim(project, 48),
        'target_workspace_name': project,
        'watch_candidate': candidate,
        'terminal_name': selected.get('terminalName', ''),
        'workspace_names': [Path(p).name for p in selected.get('workspace', [])]
    }
    ticket = None
    matches = []
    for row in records:
        if not 0 <= time.time() - row.get('timestamp', 0) < 5:
            continue
        for terminal in row.get('terminals', []):
            pid = terminal.get('pid')
            if pid in lineage and terminal.get('start') == lineage[pid]:
                matches.append(terminal)
    matches = list({(m['pid'], m['start']): m for m in matches}.values())
    if len(matches) == 1:
        ticket = {'kind': 'existing-terminal', 'terminalPid': matches[0]['pid'],
                  'terminalStart': matches[0]['start'], 'session': sid,
                  'created': time.time(), 'clientPid': next(iter(lineage)),
                  'clientStart': next(iter(lineage.values()))}
    if ticket is not None:
        token = str(uuid.uuid4())
        tickets = ROOT / 'click-tickets'
        tickets.mkdir(parents=True, exist_ok=True)
        (tickets / (token + '.json')).write_text(json.dumps(ticket))
        payload['launch_uri'] = 'codex-session://focus/' + token
    else:
        log('click-unavailable', session_id=sid, source=data.get('source'),
            detail='Cannot identify the originating terminal')
    command = (ROOT / 'windows.json').read_text()
    windows = json.loads(command)
    args = [windows.get('powershell', PS), '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden',
            '-ExecutionPolicy', 'Bypass', '-File', windows['script']]
    if not test and not claim_turn(sid, turn_id):
        return
    try:
        result = subprocess.run(args, input=json.dumps(payload, ensure_ascii=False),
                                encoding='utf-8', capture_output=True, timeout=20)
    except Exception:
        release_turn(sid, turn_id)
        raise
    if result.returncode:
        release_turn(sid, turn_id)
        log('error', session_id=sid, turn_id=turn_id, origin=origin, detail=result.stderr[-4000:])
        if test:
            raise SystemExit(result.stderr or 'Windows notification failed')
    else:
        try:
            response = json.loads(result.stdout.strip())
        except ValueError:
            response = {'status': 'sent'}
        log(response.get('status', 'sent'), session_id=sid, turn_id=turn_id, origin=origin, title=payload['title'],
            reason=response.get('reason', 'Windows toast submitted'),
            click_kind=ticket.get('kind') if ticket else None, launch_uri=payload.get('launch_uri'))
        if test:
            print(result.stdout.strip() or 'Test toast sent.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        log('error', detail=str(error))
        if '--test' in sys.argv:
            raise
