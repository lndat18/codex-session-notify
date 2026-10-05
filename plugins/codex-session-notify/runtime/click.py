"""Focus an existing Codex terminal; never open an editor or start a session."""
import datetime
import json
from pathlib import Path
import sys
import time
import uuid
ROOT = Path(__file__).resolve().parent


def log(status, **fields):
    with (ROOT / 'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'time': datetime.datetime.now().isoformat(), 'status': status, **fields}) + '\n')


def main():
    token = str(uuid.UUID(sys.argv[1]))
    ticket = json.loads((ROOT / 'click-tickets' / (token + '.json')).read_text())
    if not 0 <= time.time() - ticket['created'] <= 86400:
        raise ValueError('This notification has expired.')
    if ticket.get('kind') != 'existing-terminal':
        raise ValueError('This old notification needs a new completion notification.')
    ticket['kind'] = 'existing-terminal'
    stat = Path(f"/proc/{ticket['clientPid']}/stat").read_text()
    start = stat[stat.rfind(')') + 2:].split()[19]
    if start != ticket['clientStart']:
        raise ValueError('The originating Codex process has closed.')
    candidates = []
    for path in (ROOT / 'terminal-windows').glob('*.json'):
        try:
            row = json.loads(path.read_text())
            if not 0 <= time.time() - row.get('timestamp', 0) < 5:
                continue
            if any(t.get('pid') == ticket['terminalPid'] and t.get('start') == ticket['terminalStart']
                   for t in row.get('terminals', [])):
                candidates.append(row)
        except (OSError, ValueError):
            continue
    if len(candidates) != 1:
        raise ValueError(f'Cannot locate original terminal window: {len(candidates)} candidates')
    ticket['instance'] = candidates[0]['instance']
    ticket['requested'] = time.time()
    log('click-received', session_id=ticket['session'], kind=ticket['kind'], token=token)
    requests = ROOT / 'terminal-click-requests'
    requests.mkdir(exist_ok=True)
    request = requests / (token + '.json')
    ack = Path(str(request) + '.ack')
    ack.unlink(missing_ok=True)
    temp = request.with_suffix('.tmp')
    temp.write_text(json.dumps(ticket))
    temp.replace(request)
    try:
        for _ in range(150):
            if ack.exists():
                response = json.loads(ack.read_text())
                if response.get('status') != 'terminal-focused':
                    raise ValueError(response.get('detail', 'Terminal focus failed'))
                log('click-opened', session_id=ticket['session'], kind=ticket['kind'], response=response)
                print(json.dumps(response))
                return
            time.sleep(0.1)
        raise ValueError('VS Code did not acknowledge the terminal focus request.')
    finally:
        request.unlink(missing_ok=True)
        ack.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        log('click-error', detail=str(error))
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
