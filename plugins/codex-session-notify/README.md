# Codex Session Notifications 1.0.0

Thông báo Windows khi Codex CLI trả lời xong. Bấm thông báo để quay lại **cửa sổ VS Code và terminal đang chạy session đó**. Giữ nguyên cửa sổ phóng to và chạy bộ xử lý ẩn.

## Cài đặt

Cần Windows 10/11, WSL có systemd user, VS Code Remote WSL, Codex CLI và Python 3.11 trở lên. Bản 1.0 dùng thư mục Codex mặc định `~/.codex`.

Giải nén gói ZIP, mở terminal **WSL trong VS Code** tại thư mục vừa giải nén và chạy:

```bash
python3 plugins/codex-session-notify/install.py install
```

Bộ cài tự nhận diện máy và tài khoản; không cần sửa username, distro, đường dẫn hoặc PID. Nếu chưa thấy bản ghi terminal, chạy **Developer: Reload Window** một lần trong các cửa sổ VS Code WSL.

Nếu đã có `notify` hook riêng, bộ cài dừng trước khi sửa. Chỉ dùng `install --replace-notify` khi muốn thay hook đó. Bản sao lưu được giữ lại.

## Dùng như plugin Codex

Chạy từ thư mục gốc của gói giải nén:

```bash
codex plugin marketplace add .
codex plugin add codex-session-notify@local-notifications
```

Trong session Codex tiếp theo, gọi skill **`$codex-session-notify:session-notify`**, hoặc yêu cầu Codex kiểm tra/cài thông báo bằng plugin này.

Plugin chứa skill và bộ cài; dịch vụ thông báo được cài riêng vào máy và tiếp tục chạy qua những lần mở Codex sau. Tắt plugin trong danh sách Codex không tự tắt dịch vụ thông báo.

## Kiểm tra, cập nhật và gỡ bỏ

```bash
python3 plugins/codex-session-notify/install.py status
python3 plugins/codex-session-notify/install.py install --dry-run
python3 plugins/codex-session-notify/install.py install
python3 plugins/codex-session-notify/install.py uninstall --dry-run
python3 plugins/codex-session-notify/install.py uninstall
```

Cài lại sẽ cập nhật và sao lưu. Gỡ bỏ dừng dịch vụ, gỡ extension hỗ trợ và xóa các đăng ký thông báo của gói. Chỉ khôi phục các giá trị cấu hình thông báo còn giống giá trị gói đã cài; giữ log và bản sao lưu.

## Phạm vi và giới hạn

- Dùng cho **Codex CLI trong terminal VS Code WSL**, không phải khung chat Codex IDE hoặc Codex desktop.
- Nhiều cửa sổ VS Code cho các dự án khác nhau được hỗ trợ. Mỗi cwd dự án cần có **một Codex CLI đang hoạt động** để tự xác định terminal. Nhiều CLI trong cùng cwd chưa được ghép session chính xác; khi không xác định được thì thông báo không có đích bấm.
- Hai cửa sổ VS Code có cùng tên thư mục dự án có thể làm việc chọn native window bị mơ hồ. Bộ cài dùng window handle và thời điểm khởi tạo process sau khi chọn duy nhất; không chọn ngẫu nhiên.
- Terminal hoặc cửa sổ đã đóng sẽ không được tạo lại. Thông báo cũ trước khi cài gói mới có thể cần thay bằng thông báo mới.
- Systemd khởi động dịch vụ khi WSL chạy; gói không khởi động WSL lúc Windows đăng nhập.
- Khi Windows từ chối focus, helper thử một cặp phím ALT cân bằng để cho phép kích hoạt cửa sổ, chỉ khi không có phím bổ trợ đang giữ; helper kiểm tra native HWND thực sự ở phía trước.

## Dữ liệu và thành phần

Không dùng API key, không tải dữ liệu lên dịch vụ bên ngoài. Gói phân phối chỉ chứa mã nguồn, icon và extension VSIX, không có lịch sử chat, thông tin đăng nhập, PID thử nghiệm hoặc log của máy tác giả. Khi hoạt động, log trên máy chứa session ID và đoạn xem trước câu trả lời; có thể xóa log khi không cần.

- Runtime: `~/.codex/session-notify/`.
- Sao lưu WSL: `~/.codex/session-notify-backups/`.
- Unit: `codex-session-notify.service` của systemd user.
- Windows helper và log: `%LOCALAPPDATA%\CodexSessionNotify\`.
- Registry: `HKCU\Software\Classes\codex-session` và AppUserModelId `CodexCLI.SessionNotify`.
- VS Code extension: `local-wsl.codex-existing-terminal-focus`.

`events.jsonl` xác nhận bước chọn terminal; `native-focus.jsonl` với trạng thái **activated** mới xác nhận đúng cửa sổ đã lên trước.

## Đóng gói lại

```bash
python3 plugins/codex-session-notify/build.py
```

Tạo VSIX, ZIP và SHA-256 bằng Python chuẩn, không cần npm hay mạng. Bộ cài biên dịch helper C# trên Windows bằng Windows PowerShell.
