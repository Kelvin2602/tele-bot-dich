# Khởi động bot

## Lệnh duy nhất cần nhớ

```powershell
python -m tele_bot_dich
```

Chạy được từ **bất kỳ thư mục nào** — không cần `cd` vào project, không cần set `PYTHONPATH`.

## Yêu cầu môi trường (đã cấu hình sẵn 1 lần)

- File `.env` nằm trong `D:\tele-bot-dich\.env` chứa:
  - `TELEGRAM_BOT_TOKEN`
  - `OPENAI_API_KEY` (opencode.ai/zen, iamhc.cn, aiping.cn, OpenRouter, ...)
  - `OPENAI_BASE_URL` (vd: `https://opencode.ai/zen/v1`)
  - `OPENAI_MODEL` (vd: `mimo-v2.5-free`)
- Package đã cài editable vào site-packages:

  ```powershell
  cd D:\tele-bot-dich
  pip install -e .
  ```

  Sau đó từ mọi nơi đều chạy được `python -m tele_bot_dich`.

## Dừng bot

```powershell
# Kill tất cả python process
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

Hoặc mở Task Manager → tab Details → tìm `python.exe` (cột CommandLine có `tele_bot_dich`) → End task.

## Chạy với log ra file (foreground, dễ theo dõi)

```powershell
python -m tele_bot_dich 2>&1 | Tee-Object -FilePath d:\tele-bot-dich\bot_runtime.log
```

Log sẽ in ra terminal **đồng thời** ghi vào `bot_runtime.log`.

## Test nhanh trên Telegram

1. Mở Telegram, tìm bot theo username đã tạo với @BotFather.
2. Gửi `/start` — bot chào + hướng dẫn.
3. Click **Menu** (≡) cạnh thanh nhập tin nhắn → thấy 7 lệnh.
4. Gửi `/zh` → bot confirm `zh` → gửi `Xin chào` → bot dịch `你好，朋友`.

## Các lệnh khả dụng

| Lệnh | Chức năng |
|------|-----------|
| `/start` | Chào mừng |
| `/help` | Hướng dẫn |
| `/settings` | Cài đặt + 10 ngôn ngữ phổ biến |
| `/target` | Xem target hiện tại |
| `/set_target <code>` | Đặt target (vd: `/set_target en`) |
| `/zh` | Quick: dịch sang Tiếng Trung |
| `/da` | Quick: dịch sang Tiếng Đan Mạch |
| Tin nhắn văn bản | Dịch sang target |

## Lưu ý

- Chỉ chạy **1 instance** bot tại 1 thời điểm (Telegram giới hạn 1 polling per token).
- Log file tại `d:\tele-bot-dich\bot_runtime.log` (nếu dùng Tee-Object).
- Token Telegram + API key hiện đang nằm trong `.env` ở local — **không commit lên git** (đã có trong `.gitignore`).
- Provider hiện tại: `opencode.ai/zen` + `mimo-v2.5-free` (avg 1.88s/request).
- Tất cả **32/32 tests pass**.
- Các file test/provider cũ đã được dọn vào `_archive/` — xem thư mục `_archive/` ở root.
