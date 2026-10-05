const vscode = require('vscode');
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
function activate(context) {
  const root = path.join(os.homedir(), '.codex', 'session-notify');
  const records = path.join(root, 'terminal-windows');
  const requests = path.join(root, 'terminal-click-requests');
  fs.mkdirSync(records, { recursive: true });
  fs.mkdirSync(requests, { recursive: true });
  const instance = crypto.randomUUID();
  const record = path.join(records, instance + '.json');
  let disposed = false;
  let busy = false;
  function start(pid) {
    try {
      const stat = fs.readFileSync(`/proc/${pid}/stat`, 'utf8');
      return stat.slice(stat.lastIndexOf(')') + 2).split(' ')[19];
    } catch (_) { return null; }
  }
  async function refresh() {
    if (busy || disposed) return;
    busy = true;
    try {
      const terminals = [];
      for (const terminal of vscode.window.terminals) {
        const pid = await terminal.processId;
        terminals.push({ terminal, pid, start: start(pid), name: terminal.name });
      }
      if (disposed) return;
      const workspace = vscode.workspace.workspaceFolders?.map(f => f.uri.fsPath) || [];
      const active = vscode.window.activeTerminal;
      const activeRow = terminals.find(t => t.terminal === active);
      const focus = { instance, workspace, timestamp: Date.now() / 1000,
        focused: vscode.window.state.focused, terminalPid: activeRow?.pid || null,
        terminalStart: activeRow?.start || null, terminalName: activeRow?.name || '',
        terminals: terminals.map(t => ({pid:t.pid,start:t.start})) };
      const focusDir = path.join(root, 'focus');
      fs.mkdirSync(focusDir, { recursive: true });
      const focusFile = path.join(focusDir, instance + '.json');
      fs.writeFileSync(focusFile + '.tmp', JSON.stringify(focus));
      fs.renameSync(focusFile + '.tmp', focusFile);
      fs.writeFileSync(record + '.tmp', JSON.stringify({ instance, workspace,
        timestamp: Date.now() / 1000, focused: vscode.window.state.focused,
        terminals: terminals.map(({ terminal, ...value }) => value) }));
      fs.renameSync(record + '.tmp', record);
      for (const name of fs.readdirSync(requests)) {
        if (!/^[0-9a-f-]{36}\.json$/.test(name)) continue;
        const file = path.join(requests, name);
        if (fs.existsSync(file + '.ack')) continue;
        let request;
        try { request = JSON.parse(fs.readFileSync(file, 'utf8')); }
        catch (_) { continue; }
        if (request.instance !== instance || request.kind !== 'existing-terminal' ||
            !Number.isFinite(request.requested) || Math.abs(Date.now() / 1000 - request.requested) > 20) continue;
        let ack;
        try {
          const match = terminals.find(t => t.pid === request.terminalPid && t.start === request.terminalStart);
          if (!match) throw new Error('The original terminal is closed');
          match.terminal.show(false);
          await vscode.commands.executeCommand('workbench.action.terminal.focus');
          ack = { status: 'terminal-focused', session: request.session, terminalPid: match.pid,
            terminalName: match.name, workspace, instance };
        } catch (error) { ack = { status: 'error', detail: String(error) }; }
        fs.writeFileSync(file + '.ack.tmp', JSON.stringify(ack));
        fs.renameSync(file + '.ack.tmp', file + '.ack');
      }
    } finally { busy = false; }
  }
  function tick() { refresh().catch(() => {}); }
  const timer = setInterval(tick, 300);
  context.subscriptions.push(vscode.window.onDidChangeActiveTerminal(tick),
    vscode.window.onDidChangeWindowState(tick),
    { dispose() { disposed = true; clearInterval(timer); try { fs.unlinkSync(record); } catch (_) {}
      try { fs.unlinkSync(path.join(root, 'focus', instance + '.json')); } catch (_) {} } });
  tick();
}
module.exports = { activate };
