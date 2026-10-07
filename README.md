# Codex Session Notifications

## Terminal install / Cài từ terminal

Open a WSL terminal and paste one line / Mở terminal WSL và dán một dòng:

```bash
git clone https://github.com/lndat18/codex-session-notify.git && bash codex-session-notify/install.sh
```

**English:** The installer checks your environment, then asks only about notifications and the optional Codex management skill. Answer `yes` or `no`. Choosing notifications installs all required components together; if needed, it installs VS Code WSL support and opens the WSL folder automatically. An existing notification hook requires an additional Yes/No choice before backup and replacement.

**Tiếng Việt:** Bộ cài tự kiểm tra môi trường, rồi hỏi **“Cài thông báo Codex?”** và **“Thêm skill quản lý vào Codex?”**. Chỉ cần trả lời `yes` hoặc `no`. Khi đồng ý cài thông báo, bộ cài tự thiết lập mọi thành phần cần thiết; nếu cần, tự cài hỗ trợ WSL và mở VS Code WSL. Nếu có hook thông báo cũ, bộ cài hỏi riêng trước khi sao lưu và thay thế.

Requires Windows + WSL, Git, Python 3.11+, VS Code, Codex CLI, WSL interop and a running systemd user session. Uses the default `~/.codex`. Missing prerequisites are reported before installation; the installer does not provision WSL, Python, VS Code or Codex CLI. Nothing is published to PyPI or npm.

Máy cần có sẵn Windows + WSL, Git, Python 3.11+, VS Code, Codex CLI, WSL interop và systemd user hoạt động. Dùng `~/.codex` mặc định. Nếu thiếu điều kiện, bộ cài báo trước khi cài. Gói được phân phối trực tiếp trên GitHub, không cần PyPI hay npm.

Already cloned / Đã clone trước đó:

```bash
bash codex-session-notify/install.sh
```

Update from inside the cloned repository / Cập nhật từ thư mục repo đã clone:

```bash
git pull --ff-only && bash install.sh
```

The installer keeps a permanent source copy under `~/.local/share/codex-session-notify`; you can remove the downloaded clone after installation. Git clone alone downloads files and does not execute installers.

Bộ cài lưu một bản nguồn lâu dài tại `~/.local/share/codex-session-notify`; có thể xoá thư mục tải về sau khi cài. Riêng `git clone` không tự chạy bộ cài.

## Install with clicks / Cài đặt bằng chuột

**English:** Download the ZIP from [the latest release](https://github.com/lndat18/codex-session-notify/releases/latest), extract it, double-click **Install.cmd**, and choose **Yes**. If you have several WSL distributions, select one. The installer sets up the WSL extension, notification service, Windows click handler, and optional Codex plugin registration automatically. It keeps a permanent copy, so you can delete the extracted download afterwards. Existing notification hooks require a separate Yes/No choice and are backed up.

**Vietnamese:** Tải ZIP từ [bản phát hành mới nhất](https://github.com/lndat18/codex-session-notify/releases/latest), giải nén, bấm đúp **Install.cmd** và chọn **Yes**. Nếu có nhiều bản WSL, chọn bản muốn dùng. Bộ cài tự cài extension WSL, dịch vụ thông báo, xử lý click Windows và đăng ký plugin Codex nếu CLI hỗ trợ. Có thể xoá thư mục tải về sau khi cài. Nếu đã có cấu hình thông báo, bộ cài hỏi Yes/No trước khi sao lưu và thay thế.

Máy cần có sẵn Windows + WSL, Python 3.11+, VS Code, Codex CLI và systemd trong WSL. Bộ cài áp dụng cho tất cả session được hỗ trợ của người dùng WSL đã chọn.

Requires an existing Windows + WSL installation, Python 3.11+, VS Code, Codex CLI and WSL systemd. The wizard installs the VS Code WSL extension automatically; it does not provision Linux or Python. Applies to all supported sessions for the selected WSL user. Windows may ask you to allow a downloaded script. Only run installers you trust.


Windows notifications for Codex CLI in VS Code + WSL. Click a notification to return to the original VS Code window and existing terminal.

Thông báo Windows cho Codex CLI trong VS Code + WSL. Bấm thông báo để quay lại đúng cửa sổ VS Code và terminal đang chạy session đó.

## Table of Contents / Mục lục

- [Reliability updates / Cập nhật độ tin cậy](#reliability-updates--cập-nhật-độ-tin-cậy-111)
- [Existing skill / Skill đã cài](#existing-skill--skill-đã-cài)
- [Terminal install / Cài từ terminal](#terminal-install--cài-từ-terminal)
- [Install with clicks / Cài đặt bằng chuột](#install-with-clicks--cài-đặt-bằng-chuột)
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

Use the [one-line terminal installer](#terminal-install--cài-từ-terminal). It checks prerequisites, asks for notifications, sets up their required components, and offers the optional Codex management skill.

An existing notification hook is replaced only after a separate confirmation and backup. If terminal records do not appear after installation, run **Developer: Reload Window** once in the affected VS Code WSL window.

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

Dùng [bộ cài một dòng từ terminal](#terminal-install--cài-từ-terminal). Bộ cài tự kiểm tra điều kiện, hỏi cài thông báo, tự thiết lập các thành phần cần thiết và hỏi thêm skill quản lý Codex.

Hook thông báo cũ chỉ được thay khi bạn đồng ý riêng và đã có bản sao lưu. Nếu chưa có bản ghi terminal, chạy **Developer: Reload Window** một lần trong cửa sổ VS Code WSL đó.

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

## Reliability updates / Cập nhật độ tin cậy (1.1.1)

**English:** Each WSL distro/user has its own Windows installation directory. Every new click ticket retains its originating bridge configuration; installing another distribution preserves earlier routing. Workspace names travel as UTF-8 JSON encoded with Base64. Installation snapshots owned Windows files, registrations and shortcut before changes, restoring them if a later step fails. Concurrent installs are refused until the transaction finishes. Releases include only explicitly listed public files and the generated VSIX.

**Tiếng Việt:** Mỗi bản WSL/tài khoản có thư mục cài Windows riêng. Mỗi thông báo mới giữ cấu hình đích của chính nó; cài thêm WSL không ghi đè đích cũ. Tên thư mục được truyền bằng JSON UTF-8 mã hoá Base64. Bộ cài sao lưu file Windows, registry và shortcut trước khi thay đổi, tự khôi phục nếu bước sau thất bại. Không cho hai bộ cài chạy đồng thời. ZIP chỉ chứa danh sách file công khai được cho phép và VSIX được tạo.

Upgrade each existing WSL installation to obtain these guarantees for new notifications. Old tickets continue using legacy routing when present. If Windows rollback fails, the installer reports the error and retains its backup and transaction lock; do not delete the lock until recovery is complete. Gỡ một bản WSL giữ bộ xử lý chung khi còn bản khác hoặc cấu hình legacy; log và backup vẫn được lưu.

## Existing skill / Skill đã cài

The installer reuses and updates a compatible local marketplace registration, preserving its catalog and other plugins. An unrelated marketplace with the same name is left intact; a dedicated installer catalog is used instead. Notification installation remains independent of skill registration.

Bộ cài dùng lại và cập nhật marketplace local phù hợp đã có, giữ danh mục và các plugin khác. Nếu marketplace trùng tên thuộc nguồn khác, bộ cài giữ nguyên nguồn đó và dùng danh mục riêng.

To finish a failed optional skill step without reinstalling notifications / Hoàn tất bước thêm skill bị lỗi mà không cài lại thông báo:

```bash
python3 bootstrap.py --skill-only
```

### First completion visibility / Hiển thị câu trả lời đầu tiên

Suppression uses a fresh active terminal PID/start snapshot and verifies the actual foreground Windows window plus visible terminal. It does not require the extension focus flag to have updated first. Startup discovery and accessibility nodes receive a short bounded retry; ambiguous or unavailable identity continues to notify.

Ẩn thông báo dựa trên bản ghi terminal đang hoạt động còn mới, đối chiếu cửa sổ Windows thực sự ở phía trước và terminal đang hiển thị. Không chờ cờ focus của extension cập nhật. Có thử lại ngắn khi terminal hoặc accessibility vừa khởi tạo; nếu không xác định được đích, thông báo vẫn được gửi.

## Multiple terminals / Nhiều terminal

The installer automatically adds an owned `codex` shell function to Bash and
Zsh startup files. After installation, open a new terminal and use the normal
commands:

```bash
codex
codex resume
```

No manual launcher command is required. Existing terminal shells and already
running Codex sessions keep their previous settings; reopen/resume them to use
the update. New local interactive sessions use `--no-daemon` and a notification
hook whose process ancestry identifies the original terminal. Administrative
commands, noninteractive jobs, remote clients, and explicit notify overrides
are passed through. Remote or overridden-hook sessions do not have this exact
routing guarantee. Closed terminals are not reopened.

The installer backs up shell configuration and rolls it back if installation
fails. Reinstallation replaces only its marked block; uninstall removes that
block. Existing unrelated `codex` shell functions are preserved by refusing a
conflicting automatic integration.

**Tiếng Việt:** Chỉ cần cài bằng `bash install.sh`, sau đó mở terminal mới và gõ
`codex` như bình thường ở mọi dự án. Không cần chạy `launch.py` nữa. Muốn tiếp tục
session cũ, dùng `codex resume`. Terminal/session đang mở cần khởi động lại để
nhận cấu hình mới.

Verification: 19 automated tests pass. Windows click activation still requires
manual end-to-end verification.
