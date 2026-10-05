# Codex Session Notifications

Windows notifications for Codex CLI in VS Code + WSL. Click a notification to return to the original VS Code window and existing terminal.

Thông báo Windows cho Codex CLI trong VS Code + WSL. Bấm thông báo để quay lại đúng cửa sổ VS Code và terminal đang chạy session đó.

## Table of Contents / Mục lục

- [English](#english)
  - [Features](#features)
  - [Global installation scope](#global-installation-scope)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Usage and maintenance](#usage-and-maintenance)
  - [Limitations](#limitations)
- [Vietnamese / Tiếng Việt](#vietnamese--tiếng-việt)
  - [Tính năng](#tính-năng)
  - [Phạm vi cài đặt toàn hệ thống](#phạm-vi-cài-đặt-toàn-hệ-thống)
  - [Yêu cầu](#yêu-cầu)
  - [Cài đặt](#cài-đặt)
  - [Sử dụng và quản lý](#sử-dụng-và-quản-lý)
  - [Giới hạn](#giới-hạn)
- [Detailed documentation / Tài liệu chi tiết](#detailed-documentation--tài-liệu-chi-tiết)

## English

### Features

- Display a Windows notification when a Codex CLI turn completes, with the session title and a response preview.
- Click to select the original terminal and bring its VS Code window to the foreground.
- Keep maximized windows maximized and run the activation helper without a visible console.
- Suppress completion notifications when the matching terminal is visible in the focused VS Code window.
- Include a reusable Codex skill, VS Code extension, installer, update command and uninstaller.

### Global installation scope

**Install once per Windows account and WSL distribution. Notifications then apply to all supported Codex CLI sessions and projects in that environment.**

The runtime runs independently of the current conversation or repository:

| Component | Global location / scope |
| --- | --- |
| Notification runtime | `~/.codex/session-notify/` |
| Session watcher | Monitors all rollout files under `~/.codex/sessions/`, including newly created sessions |
| Background service | `codex-session-notify.service`, enabled for the WSL user |
| VS Code extension | Installed into the selected WSL extension environment; activates in its supported VS Code windows |
| Windows click handler | `%LOCALAPPDATA%\CodexSessionNotify\`, registered for the Windows account |
| Codex plugin | Installed in the user's Codex plugin cache and enabled in user configuration |

You do not need to install it again for each session, invoke the skill before every chat, or add configuration to every project. The service runs while WSL is running and starts with the user's systemd session. For another Windows account or another WSL distribution, install separately.

“Global” describes the current user's supported Codex environment. It does not monitor other applications, cover every Windows account automatically, or launch WSL at Windows login.

### Requirements

- Windows 10/11 with Windows PowerShell and WSL interop.
- WSL with a working systemd user session.
- VS Code with Remote WSL, Codex CLI, and Python 3.11 or newer.
- The default Codex data directory: `~/.codex`.

### Installation

Clone into a persistent location, then open a **VS Code WSL terminal**:

```bash
git clone https://github.com/lndat18/codex-session-notify.git ~/.local/share/codex-session-notify
cd ~/.local/share/codex-session-notify
python3 plugins/codex-session-notify/install.py install
```

Alternatively, download the ZIP from [Releases](https://github.com/lndat18/codex-session-notify/releases), extract it into a persistent directory, and run the same installer from the extracted root.

To also install the Codex skill for future installation, inspection and repair requests:

```bash
codex plugin marketplace add .
codex plugin add codex-session-notify@local-notifications
```

The installer detects the Windows account, WSL distribution and live VS Code connection. It backs up the installation and changes only the notification settings it owns. If a separate `notify` hook exists, installation stops; use `install --replace-notify` only if you intend to replace that hook.

If terminal window records do not appear after installation, run **Developer: Reload Window** once in each VS Code WSL window.

### Usage and maintenance

Start Codex CLI in any supported VS Code WSL project. Switch to another application while Codex works; when it finishes, click the new notification to return to its existing terminal. Future sessions are discovered automatically.

From the cloned or extracted repository:

```bash
# Inspect the global service and terminal windows.
python3 plugins/codex-session-notify/install.py status

# Preview an installation or update without applying it.
python3 plugins/codex-session-notify/install.py install --dry-run

# Update an existing installation, with a backup.
python3 plugins/codex-session-notify/install.py install

# Preview removal, then remove the runtime when wanted.
python3 plugins/codex-session-notify/install.py uninstall --dry-run
python3 plugins/codex-session-notify/install.py uninstall
```

In a new Codex session, use **`$codex-session-notify:session-notify`** to ask Codex to inspect, install or repair the setup. The runtime keeps running without invoking this skill. Disabling the Codex skill plugin does not stop the notification service; use the uninstaller to remove the runtime.

### Limitations

- Supports Codex CLI in VS Code WSL, rather than the Codex IDE chat panel or desktop application.
- Supports multiple project windows with distinct project names. Automatic association currently requires **one interactive Codex CLI per project working directory**. Multiple CLI processes in the same directory do not get an arbitrary click target.
- Multiple VS Code windows with the same project folder name can make native window selection ambiguous.
- Closed terminals and windows are not recreated. Old notifications from before an update may need to be replaced by new ones.
- The activation helper verifies that the target window is actually foreground. If Windows denies activation, it can send a balanced ALT key pair when no modifier is held to allow activation.

## Vietnamese / Tiếng Việt

### Tính năng

- Hiện thông báo Windows khi Codex CLI trả lời xong, kèm tên session và đoạn xem trước câu trả lời.
- Bấm thông báo để chọn đúng terminal và đưa đúng cửa sổ VS Code lên trước.
- Giữ nguyên trạng thái phóng to của cửa sổ và chạy bộ xử lý ẩn, không hiện cửa sổ console.
- Không hiện thông báo hoàn tất khi bạn đang xem đúng terminal trong cửa sổ VS Code được focus.
- Có skill Codex, extension VS Code, bộ cài, lệnh cập nhật và lệnh gỡ bỏ để tái sử dụng.

### Phạm vi cài đặt toàn hệ thống

**Cài một lần cho mỗi tài khoản Windows và bản WSL. Sau đó, thông báo áp dụng cho mọi dự án và session Codex CLI được hỗ trợ trong môi trường đó.**

Runtime hoạt động độc lập với cuộc hội thoại và repo đang mở:

| Thành phần | Vị trí / phạm vi toàn cục |
| --- | --- |
| Runtime thông báo | `~/.codex/session-notify/` |
| Bộ theo dõi session | Theo dõi mọi rollout trong `~/.codex/sessions/`, tự phát hiện session mới |
| Dịch vụ chạy nền | `codex-session-notify.service`, được bật cho tài khoản WSL |
| Extension VS Code | Cài vào môi trường extension của bản WSL đã chọn; hoạt động trong các cửa sổ VS Code được hỗ trợ của môi trường đó |
| Bộ xử lý bấm trên Windows | `%LOCALAPPDATA%\CodexSessionNotify\`, đăng ký cho tài khoản Windows |
| Plugin Codex | Cài trong plugin cache của người dùng và bật trong cấu hình người dùng |

Bạn không cần cài lại cho mỗi session, gọi skill trước mỗi cuộc chat hoặc thêm cấu hình vào từng dự án. Dịch vụ chạy khi WSL đang hoạt động và khởi động cùng phiên systemd của người dùng. Với tài khoản Windows hoặc bản WSL khác, cần cài riêng.

“Toàn hệ thống” ở đây là môi trường Codex được hỗ trợ của tài khoản hiện tại. Plugin không theo dõi các ứng dụng khác, không tự cài cho mọi tài khoản Windows và không khởi động WSL lúc Windows đăng nhập.

### Yêu cầu

- Windows 10/11, có Windows PowerShell và WSL interop.
- WSL có phiên systemd user hoạt động.
- VS Code Remote WSL, Codex CLI và Python 3.11 trở lên.
- Thư mục dữ liệu Codex mặc định: `~/.codex`.

### Cài đặt

Clone vào vị trí lưu lâu dài, rồi mở **terminal WSL trong VS Code**:

```bash
git clone https://github.com/lndat18/codex-session-notify.git ~/.local/share/codex-session-notify
cd ~/.local/share/codex-session-notify
python3 plugins/codex-session-notify/install.py install
```

Hoặc tải ZIP tại [Releases](https://github.com/lndat18/codex-session-notify/releases), giải nén vào thư mục lưu lâu dài và chạy bộ cài từ thư mục gốc của gói.

Để thêm skill Codex cho những lần yêu cầu cài đặt, kiểm tra hoặc sửa sau này:

```bash
codex plugin marketplace add .
codex plugin add codex-session-notify@local-notifications
```

Bộ cài tự nhận diện tài khoản Windows, bản WSL và kết nối VS Code đang hoạt động. Bộ cài tạo bản sao lưu và chỉ sửa các cấu hình thông báo do nó quản lý. Nếu đã có `notify` hook riêng, bộ cài dừng; chỉ dùng `install --replace-notify` khi bạn muốn thay hook đó.

Nếu chưa có bản ghi terminal sau khi cài, chạy **Developer: Reload Window** một lần trong mỗi cửa sổ VS Code WSL.

### Sử dụng và quản lý

Mở Codex CLI trong bất kỳ dự án VS Code WSL được hỗ trợ nào. Chuyển sang ứng dụng khác trong khi Codex làm việc; khi có thông báo hoàn tất, bấm để quay lại terminal đang chạy session đó. Session mới được phát hiện tự động.

Từ thư mục repo đã clone hoặc gói đã giải nén:

```bash
# Kiểm tra dịch vụ toàn cục và các cửa sổ terminal.
python3 plugins/codex-session-notify/install.py status

# Xem trước thay đổi cài đặt hoặc cập nhật.
python3 plugins/codex-session-notify/install.py install --dry-run

# Cập nhật bản đã cài, có sao lưu.
python3 plugins/codex-session-notify/install.py install

# Xem trước rồi gỡ runtime khi muốn ngừng sử dụng.
python3 plugins/codex-session-notify/install.py uninstall --dry-run
python3 plugins/codex-session-notify/install.py uninstall
```

Trong session Codex mới, gọi **`$codex-session-notify:session-notify`** để yêu cầu Codex kiểm tra, cài hoặc sửa bộ thông báo. Runtime vẫn chạy nếu không gọi skill. Tắt plugin skill trong Codex không tự tắt dịch vụ thông báo; dùng lệnh gỡ bỏ để loại bỏ runtime.

### Giới hạn

- Hỗ trợ Codex CLI trong terminal VS Code WSL; không áp dụng cho khung chat Codex IDE hoặc ứng dụng Codex desktop.
- Hỗ trợ nhiều cửa sổ dự án có tên khác nhau. Để tự xác định đúng terminal, hiện cần **một Codex CLI đang hoạt động trong mỗi thư mục làm việc của dự án**. Nếu nhiều CLI cùng chạy trong một thư mục, plugin không chọn ngẫu nhiên đích bấm.
- Nhiều cửa sổ VS Code có cùng tên thư mục dự án có thể làm việc chọn cửa sổ Windows bị mơ hồ.
- Không tạo lại terminal hoặc cửa sổ đã đóng. Thông báo cũ trước khi cập nhật có thể cần thay bằng thông báo mới.
- Bộ xử lý kiểm tra cửa sổ đích thực sự ở phía trước. Nếu Windows từ chối, bộ xử lý có thể gửi một cặp phím ALT cân bằng khi không có phím bổ trợ đang giữ để cho phép kích hoạt cửa sổ.

## Detailed documentation / Tài liệu chi tiết

See [the plugin README](plugins/codex-session-notify/README.md) for component locations, logs, backup behavior and rebuilding the ZIP/VSIX.

Xem [README của plugin](plugins/codex-session-notify/README.md) để biết vị trí thành phần, log, cách sao lưu và đóng gói lại ZIP/VSIX.
