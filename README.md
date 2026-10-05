# Codex Session Notifications

Clone repo rồi mở terminal WSL trong VS Code:

```bash
git clone https://github.com/lndat18/codex-session-notify.git
cd codex-session-notify
```

Hoặc tải ZIP trong **Releases**, giải nén và mở terminal tại thư mục gốc. Cài bằng:

```bash
python3 plugins/codex-session-notify/install.py install
codex plugin marketplace add .
codex plugin add codex-session-notify@local-notifications
```

Dùng lại trong session Codex tiếp theo bằng **`$codex-session-notify:session-notify`**.

Chi tiết, giới hạn và lệnh gỡ bỏ: [README của plugin](plugins/codex-session-notify/README.md).
