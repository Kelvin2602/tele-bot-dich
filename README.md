# Telegram Translation Bot (tele-bot-dich)

> **🔴 Bot này CHỈ làm MỘT việc: PHIÊN DỊCH. Không chat AI, không ảnh, không tính năng nào khác.**

Bot Telegram dịch văn bản tự động sang **bất kỳ ngôn ngữ nào** sử dụng OpenAI-compatible API. Hỗ trợ 100+ ngôn ngữ qua mã ISO 639-1.

> **Trạng thái hiện tại (2026-06-25):** Bot đang chạy ổn định với `opencode.ai/zen` + `mimo-v2.5-free`. Trung bình **1.88s / request**, **46/46 tests pass**.

## ✨ Tính năng

- **Dịch tự động**: gửi bất kỳ văn bản nào → bot tự phát hiện ngôn ngữ nguồn và dịch sang ngôn ngữ đích
- **Menu button** cạnh thanh nhập tin nhắn: tổng cộng **7 lệnh** (`/start`, `/help`, `/settings`, `/target`, `/set_target`, `/zh`, `/da`)
- **Quick set commands**: `/zh` (Trung), `/da` (Đan Mạch) — set target chỉ với 1 lệnh
- **Ngôn ngữ đích theo từng user**: `/set_target vi`, `/set_target ja`, ... (mặc định `vi`)
- **10 ngôn ngữ phổ biến** được gợi ý trong `/settings`
- **Auto-override thông minh**: nhắn tiếng Trung/Đan Mạch → tự động dịch sang Việt (bất kể target setting)
- **Locale prompts**: giọng Sài Gòn (vi), Bắc Kinh (zh), Copenhagen (da) cho bản dịch tự nhiên hơn
- **Fail-fast** với `max_retries=0` — tránh timeout 117s+ do retry ngầm
- Tối đa **4000 ký tự** / tin nhắn
- Phản hồi format rõ ràng: `🌍 EN → VI\n\n{bản dịch}`
- **Typing indicator** tự động refresh mỗi 4s (Telegram tự clear sau 5s)
- **Text-only UI** — không có InlineKeyboard (theo yêu cầu dự án)

## 📦 Tech stack

- Python ≥ 3.11 (đang chạy 3.14)
- [python-telegram-bot](https://docs.python-telegram-bot.org/) v22+
- [OpenAI Python SDK](https://github.com/openai/openai-python) (AsyncOpenAI)
- **OpenAI-compatible endpoints** — linh hoạt: OpenAI, DeepSeek, OpenRouter, opencode.ai/zen, custom proxy
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) cho config
- [loguru](https://loguru.readthedocs.io/) cho logging
- pytest + pytest-asyncio cho testing

## 🚀 Cài đặt

### 1. Yêu cầu

- Python 3.11+
- pip (hoặc Poetry)

### 2. Cài dependencies

```powershell
cd d:\tele-bot-dich
pip install -e .
```

### 3. Tạo bot Telegram

1. Mở Telegram, tìm **@BotFather**
2. Gửi `/newbot`, đặt tên & username
3. Lưu **token** nhận được

### 4. Tạo API key

Provider khuyến nghị hiện tại: **[opencode.ai/zen](https://opencode.ai/zen)** với model `mimo-v2.5-free` (miễn phí, ~1.88s/request).

```dotenv
OPENAI_API_KEY=sk-rzLBXcRPGSBloCJbUmTIxNgfJYdGuiPCjFBCSV4nt098fp7nrulnHV10jWsTUGpa
OPENAI_BASE_URL=https://opencode.ai/zen/v1
OPENAI_MODEL=mimo-v2.5-free
```

Provider khác được hỗ trợ (xem `.env.example`):
- OpenAI chính thức (`gpt-4o-mini`)
- aiping.cn (`GLM-4.7-Flash`)
- iamhc.cn (`step-3.7-flash`)
- OpenRouter (free hoặc paid)

### 5. Cấu hình `.env`

```powershell
cp .env.example .env
# Sửa .env: điền TELEGRAM_BOT_TOKEN và API key
```

### 6. Chạy bot

```powershell
python -m tele_bot_dich
```

Bot sẽ in log:
```
2026-06-05 21:17:07 | INFO | __main__:main:27 - Starting Telegram Translation Bot...
2026-06-05 21:17:09 | INFO | tele_bot_dich.bot:build_application:51 - Handlers registered. Ready to run.
2026-06-05 21:17:10 | INFO | __main__:_post_init:19 - Bot menu commands registered.
```

## 💬 Sử dụng

Trên Telegram, mở chat với bot:

### Menu (cạnh thanh nhập tin nhắn)

| Lệnh | Mô tả |
|------|-------|
| `/start` | Chào mừng + hướng dẫn |
| `/help` | Trợ giúp chi tiết |
| `/settings` | Cài đặt + gợi ý 10 ngôn ngữ phổ biến |
| `/target` | Xem ngôn ngữ đích hiện tại |
| `/set_target <code>` | Đặt ngôn ngữ đích (vd: `/set_target en`) |
| `/zh` | **Quick set:** dịch sang Tiếng Trung (中文) |
| `/da` | **Quick set:** dịch sang Tiếng Đan Mạch (Dansk) |

### Ví dụ workflow

```
Bạn:    /zh
Bot:    ✅ Đã đặt ngôn ngữ đích: zh

Bạn:    Xin chào bạn
Bot:    🌍 VI → ZH
        你好，朋友

Bạn:    /da
Bot:    ✅ Đã đặt ngôn ngữ đích: da

Bạn:    Xin chào bạn
Bot:    🌍 VI → DA
        Hej med dig
```

## ⚙️ Cấu hình nâng cao

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `TELEGRAM_BOT_TOKEN` | (bắt buộc) | Token từ @BotFather |
| `OPENAI_API_KEY` | (bắt buộc) | API key provider |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model ID |
| `OPENAI_TIMEOUT_SECONDS` | `60` | Timeout / request (giây) |
| `OPENAI_MAX_RETRIES` | `0` | Retry tự động của OpenAI SDK (0 = fail-fast) |
| `ENABLE_THINKING` | `false` | Tắt thinking mode (pass qua `extra_body`) |
| `DEFAULT_TARGET_LANG` | `vi` | Target mặc định khi user mới |
| `MAX_TEXT_LENGTH` | `4000` | Giới hạn ký tự / tin nhắn |
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR |

## 🧪 Testing

```powershell
python -m pytest tests/ -v
```

Hiện tại: **46/46 tests pass** (handlers + translator + language detector + locale prompts + auto-override + rate limiter + integration).

## 🛠 Development

```powershell
# Lint
ruff check src tests

# Format
black src tests
```

## 📁 Cấu trúc dự án

```
tele-bot-dich/
├── src/tele_bot_dich/
│   ├── config.py                 # Pydantic Settings
│   ├── bot.py                    # Application builder + 7 handlers
│   ├── commands.py               # Menu commands (setMyCommands)
│   ├── __main__.py               # Entry point + post_init hook
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py              # /start, /help (MarkdownV2)
│   │   ├── settings.py           # /set_target, /target, /settings, /zh, /da
│   │   └── translate.py          # Dịch tin nhắn + typing indicator
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_translator.py  # AsyncOpenAI + extra_body + max_retries
│   │   └── language_detector.py  # Unicode ranges + stopwords
│   ├── models/
│   │   ├── __init__.py
│   │   └── user_settings.py      # In-memory store
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # loguru config
│       └── formatters.py         # format_translation_reply
├── tests/                        # 32/32 tests
├── _archive/                     # Lưu trữ file test/provider cũ
│   ├── scripts/
│   ├── logs/
│   └── test_data/
├── docs/
│   ├── openapi.yaml              # OpenAPI 3.1 contract
│   ├── TODO.md                   # Lịch sử UI/UX + reset
│   └── ghi chú.md                # Hướng dẫn chạy bot
├── PLAN.md                       # Kế hoạch chi tiết
├── pyproject.toml
└── .env.example
```

## 🔄 Lịch sử provider

| Ngày | Provider | Model | Ghi chú |
|------|----------|-------|---------|
| 2026-06-05 | opencode.ai/zen | **mimo-v2.5-free** ⚡ | Hiện tại, ~1.88s |
| 2026-06-05 | aiping.cn | GLM-4.7-Flash | Backup, cold start 60-90s |
| 2026-06-05 | iamhc.cn | step-3.5-flash | Thay đổi nhiều lần |
| 2026-06-05 | OpenRouter | openai/gpt-oss-20b:free | Rate limit 429 |
| 2026-06-05 | opencode.ai/zen | deepseek-v4-flash-free | 500 server errors |

Xem chi tiết tại [PLAN.md](./PLAN.md).

## 🐛 Troubleshooting

### Bot conflict: "terminated by other getUpdates request"

Có 2 instance bot đang chạy. Kill hết:
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Timeout 60s

Một số model trên free tier có cold start chậm. Cân nhắc:
- Tăng `OPENAI_TIMEOUT_SECONDS=120`
- Chuyển sang `mimo-v2.5-free` (warm ngay)

### Menu button không hiện

- Restart bot (gọi `setMyCommands` qua `post_init`)
- Kiểm tra log: `Bot menu commands registered`

## 📜 License

MIT
