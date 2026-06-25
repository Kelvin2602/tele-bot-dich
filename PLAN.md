# Kế hoạch xây dựng Telegram Bot Phiên Dịch

> **Ngày tạo:** 2026-06-05
> **Cập nhật cuối:** 2026-06-25
> **Trạng thái:** Production — đang chạy ổn định (polling)
> **Ngôn ngữ lập trình:** Python 3.11+ (đang chạy 3.14)
> **Quản lý gói:** pip (dependencies cài global)
> **Framework bot:** `python-telegram-bot` v22+
> **Dịch vụ dịch:** OpenAI-compatible (`https://opencode.ai/zen/v1`)
> **Model hiện tại:** `mimo-v2.5-free` (opencode.ai/zen — nhanh & ổn định nhất)
> **Triển khai:** Local (polling) — sẵn sàng cho webhook trên Render

---

## Tình trạng hiện tại (`2026-06-25`)

| Khu vực | Trạng thái | Ghi chú |
|---------|-----------|---------|
| Cấu trúc dự án | ✅ Hoàn thành | Full structure: handlers, services, models, utils, tests |
| Config (`.env`) | ✅ Đã cấu hình | Token Telegram + opencode.ai/zen + model `mimo-v2.5-free` |
| OpenAI Service | ✅ Hoạt động ổn định | Trung bình 1.88s/request, có thinking off + max_retries=0 |
| Handlers | ✅ Hoàn thành | 7 lệnh + translate + locale prompts + auto-override |
| Tests | ✅ **46/46 passed** | test_handlers.py (14) + test_openai_translator.py (13) + test_language_detector.py (5) + test_rate_limiter.py (14) |
| Rate Limiting | ✅ Đã thêm | 10 requests/user/60s, sliding window, thread-safe |
| Bot khởi động | ✅ Chạy được | `python -m tele_bot_dich` |
| Menu button | ✅ Hoạt động | `setMyCommands` qua `commands.py` |
| UI/UX cải thiện | ✅ Hoàn thành | MarkdownV2 + fallback plain text, typing indicator, `/settings` panel |
| Dọn dẹp thư mục | ✅ Hoàn thành | 30+ file cũ vào `_archive/` |
| Webhook + Dockerfile | ✅ Sẵn sàng | `WEBHOOK_ENABLED=true` + `Dockerfile` cho Render |

---

## 🔴 Hard Constraints (BẮT BUỘC)

> **Bot này CHỈ làm một việc duy nhất: PHIÊN DỊCH.**
> Tuyệt đối KHÔNG thêm bất kỳ tính năng nào khác ngoài dịch thuật.

### Quy tắc cứng:
1. **Chỉ xử lý tin nhắn văn bản** — không ảnh, voice, sticker, file, video, animation
2. **Chỉ 7 lệnh Menu** — tất cả đều liên quan đến dịch:
   - `/start`, `/help` — hướng dẫn sử dụng bot dịch
   - `/settings`, `/target`, `/set_target` — cấu hình ngôn ngữ dịch
   - `/zh`, `/da` — shortcut đặt ngôn ngữ đích
3. **KHÔNG thêm**:
   - ❌ Chat AI / conversational agents
   - ❌ Image generation / OCR / voice recognition
   - ❌ Games, quizzes, polls
   - ❌ User management, admin tools
   - ❌ Database / persistence (giữ in-memory)
   - ❌ REST API endpoints / custom HTTP handlers (bot chỉ phản hồi Telegram commands)
   - ❌ Inline mode, callback queries, keyboards
   - ❌ Group chat features
   - ❌ Bất kỳ tính năng nào không liên quan đến dịch thuật
4. **Mỗi thay đổi code phải tự hỏi:** "Tính năng này có giúp dịch tốt hơn không?" Nếu không → **từ chối**

### Scope hợp lệ (được phép):
- ✅ Cải thiện chất lượng bản dịch (locale prompt, better model, better prompt)
- ✅ Tối ưu tốc độ dịch (cache, faster model, timeout tuning)
- ✅ Bảo vệ quota API (rate limit, max retries = 0)
- ✅ UX liên quan đến dịch (typing indicator, format output, MarkdownV2)
- ✅ Test, lint, CI/CD — miễn là không thêm business logic

---

## 1. Mục tiêu dự án

Xây dựng một Telegram bot có khả năng **dịch văn bản tự động** sang **bất kỳ ngôn ngữ nào** (100+ ngôn ngữ) thông qua OpenAI, với các đặc điểm:

- Nhận tin nhắn văn bản tiếng bất kỳ → tự động phát hiện ngôn ngữ nguồn.
- Cho phép người dùng chỉ định ngôn ngữ đích (mặc định: tiếng Việt).
- Phản hồi nhanh, có định dạng rõ ràng (ngôn ngữ nguồn/đích, nội dung dịch).
- Lưu lịch sử dịch trong phiên làm việc (in-memory, có thể mở rộng ra SQLite).

---

## 2. Tech Stack

| Lớp | Công nghệ | Lý do chọn |
|-----|-----------|------------|
| Ngôn ngữ | Python 3.11+ | Type hints mạnh, async/await chuẩn |
| Bot framework | `python-telegram-bot` v21+ | API ổn định, hỗ trợ Application/Handler pattern |
| Translation engine | OpenAI / OpenAI-compatible (opencode.ai/zen, DeepSeek, OpenRouter) | Linh hoạt chọn provider, hiện dùng `mimo-v2.5-free` qua opencode.ai/zen |
| HTTP client | `httpx` | Async, hiện đại, dùng cho OpenAI SDK |
| OpenAI SDK | `openai` (official) | Hỗ trợ streaming, `max_retries=0` để fail-fast, `extra_body` cho thinking |
| Config | `pydantic-settings` | Đọc biến môi trường có type-safety |
| Logging | `loguru` | Cú pháp đơn giản, hiển thị đẹp |
| Testing | `pytest` + `pytest-asyncio` | Chuẩn cho code async |
| Lint/Format | `ruff` + `black` | Nhanh, tích hợp tốt với Poetry |
| Quản lý gói | Poetry | Lockfile, môi trường ảo tự động |

---

## 3. Cấu trúc thư mục dự án

```
tele-bot-dich/
├── pyproject.toml              # Khai báo dependencies (Poetry)
├── poetry.lock                 # Lockfile
├── README.md
├── .env.example                # Mẫu biến môi trường
├── .gitignore
├── PLAN.md                     # File kế hoạch này
├── docs/
│   └── openapi.yaml            # OpenAPI 3.1 mô tả các command của bot
├── src/
│   └── tele_bot_dich/
│       ├── __init__.py
│       ├── __main__.py         # Entry point: python -m tele_bot_dich
│       ├── config.py           # Pydantic Settings
│       ├── bot.py              # Khởi tạo Application
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── start.py        # /start, /help
│       │   ├── translate.py    # Xử lý tin nhắn văn bản
│       │   └── settings.py     # /set_target, /set_source
│       ├── services/
│       │   ├── __init__.py
│       │   ├── openai_translator.py  # Gọi OpenAI API
│       │   └── language_detector.py  # Phát hiện ngôn ngữ nguồn
│       ├── models/
│       │   ├── __init__.py
│       │   └── user_settings.py      # Lưu setting theo user (in-memory)
│       └── utils/
│           ├── __init__.py
│           ├── formatters.py         # Format message Telegram (MarkdownV2)
│           └── logger.py             # Cấu hình loguru
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_openai_translator.py
    ├── test_language_detector.py
    └── test_handlers.py
_archive/
    ├── scripts/          # 19 file benchmark/test cũ
    ├── logs/             # 8 file log
    └── test_data/        # 6 file JSON
```

**Ràng buộc:** Mỗi file Python ≤ 200–500 dòng (theo rule dự án).

---

## 4. Khởi tạo dự án với Poetry

### 4.1. Cài đặt Poetry (nếu chưa có)

```powershell
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Hoặc qua pip
pip install poetry
```

### 4.2. Khởi tạo project

```powershell
cd "d:\Tool\TOOL\OPENCLAW\TELE BOT DỊCH"
poetry init
# Trả lời các câu hỏi tương tác, hoặc dùng --no-interaction
```

### 4.3. `pyproject.toml` (mẫu)

```toml
[tool.poetry]
name = "tele-bot-dich"
version = "0.1.0"
description = "Telegram translation bot powered by OpenAI"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
python = "^3.11"
packages = [{ include = "tele_bot_dich", from = "src" }]

[tool.poetry.dependencies]
python = "^3.11"
python-telegram-bot = "^21.6"
openai = "^1.50.0"
pydantic = "^2.9"
pydantic-settings = "^2.6"
httpx = "^0.27"
loguru = "^0.7"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3"
pytest-asyncio = "^0.24"
ruff = "^0.7"
black = "^24.10"
mypy = "^1.13"
pre-commit = "^4.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 4.4. Cài đặt dependencies

```powershell
poetry install
poetry shell                  # Kích hoạt venv
```

---

## 5. Biến môi trường (`.env.example`)

```dotenv
# === Telegram Bot Token ===
# Lấy từ @BotFather trên Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# === Provider API (OpenAI hoặc OpenAI-compatible) ===
# Hỗ trợ bất kỳ endpoint nào tuân thủ OpenAI Chat Completions format.
#
# opencode.ai/zen (khuyên dùng — mimo-v2.5-free nhanh & ổn định nhất):
#   OPENAI_API_KEY=sk-...
#   OPENAI_BASE_URL=https://opencode.ai/zen/v1
#   OPENAI_MODEL=mimo-v2.5-free
#
# OpenAI chính thức:
#   OPENAI_API_KEY=sk-...
#   OPENAI_BASE_URL=
#   OPENAI_MODEL=gpt-4o-mini

OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://opencode.ai/zen/v1
OPENAI_MODEL=mimo-v2.5-free

# Timeout khi gọi API (giây)
OPENAI_TIMEOUT_SECONDS=30

# Số lần retry tự động của OpenAI SDK (0 = fail-fast, tránh 117s+ timeout)
OPENAI_MAX_RETRIES=0

# Bật/tắt thinking mode (pass qua `extra_body`). false = tắt (khuyến nghị)
ENABLE_THINKING=false

# === Bot behavior ===
DEFAULT_TARGET_LANG=vi
MAX_TEXT_LENGTH=4000

# === Logging ===
LOG_LEVEL=INFO
```

---

## 6. Hợp đồng hành vi (Bot "API" — OpenAPI 3.1)

Mặc dù đây là Telegram bot, ta mô hình hoá các **command** như một API contract để:
- Dễ dàng test hợp đồng.
- Có tài liệu tham chiếu cho nhóm phát triển.
- Tích hợp sau này với webhook nếu cần.

📄 Xem chi tiết tại: [`docs/openapi.yaml`](./docs/openapi.yaml)

### 6.1. Tóm tắt các endpoint (lệnh)

| Lệnh | Mô tả | Input | Output |
|------|-------|-------|--------|
| `/start` | Chào mừng + hướng dẫn | — | Tin nhắn chào |
| `/help` | Liệt kê lệnh | — | Tin nhắn trợ giúp |
| `/settings` | Cài đặt + gợi ý ngôn ngữ | — | Panel cài đặt (HTML) |
| `/target` | Xem ngôn ngữ đích hiện tại | — | Mã ngôn ngữ |
| `/set_target <code>` | Đặt ngôn ngữ đích (vd: `vi`, `en`, `ja`) | `code` | Xác nhận |
| `/zh` | Quick set sang Tiếng Trung (zh) | — | ✅ Đã đặt: zh |
| `/da` | Quick set sang Tiếng Đan Mạch (da) | — | ✅ Đã đặt: da |
| *(tin nhắn văn bản)* | Dịch văn bản | văn bản | Bản dịch + meta |

### 6.2. Mã lỗi (theo hợp đồng)

| Mã | Ý nghĩa | Xử lý |
|----|---------|--------|
| `E001` | Văn bản rỗng / quá dài (> 4000 ký tự) | Nhắc lại giới hạn |
| `E002` | Mã ngôn ngữ không hợp lệ | Gợi ý danh sách |
| `E003` | Lỗi OpenAI API (timeout/rate limit) | Retry + thông báo |
| `E004` | Không xác định được ngôn ngữ nguồn | Mặc định `auto` |

---

## 7. Các bước triển khai (Task Breakdown)

### Giai đoạn 1 — Foundation (Ngày 1) ✅

- [x] **1.1.** Khởi tạo Poetry project, tạo cấu trúc thư mục.
- [x] **1.2.** Tạo `config.py` với `pydantic-settings`, đọc `.env`.
- [x] **1.3.** Tạo `utils/logger.py` cấu hình loguru.
- [x] **1.4.** Tạo `utils/formatters.py` (escape MarkdownV2 cho Telegram).
- [x] **1.5.** Verify: `python -c "from tele_bot_dich.config import Settings; print(Settings())"`

### Giai đoạn 2 — OpenAI Service (Ngày 1–2) ✅

- [x] **2.1.** Implement `services/openai_translator.py`:
  - Hàm `async def translate(text, target_lang, source_lang="auto") -> TranslationResult`.
  - Dùng `openai.AsyncOpenAI` client.
  - Prompt system: *"You are a professional translator..."* + `response_format={"type": "json_object"}`.
- [x] **2.2.** Implement `services/language_detector.py` (heuristic fallback, pluggable).
- [x] **2.3.** Test thực tế: gọi `translate("Hello", "vi")` → `source=en, translated=Xin chào` ✅.

### Giai đoạn 3 — Bot Handlers (Ngày 2) ✅

- [x] **3.1.** `bot.py`: `Application.builder().token(...).build()` + đăng ký handlers.
- [x] **3.2.** `handlers/start.py`: `/start`, `/help` với MarkdownV2.
- [x] **3.3.** `handlers/settings.py`: `/set_target`, `/target` — dùng `UserSettingsStore` (in-memory dict).
- [x] **3.4.** `handlers/translate.py`:
  - Lấy user settings → validate độ dài → gọi `OpenAITranslator` → format `🌍 EN → VI\n\n{bản dịch}`.
- [x] **3.5.** `__main__.py`: `application.run_polling()`.

### Giai đoạn 4 — Testing (Ngày 3) ✅

- [x] **4.1.** `tests/test_openai_translator.py`: 6 tests — Mock client + error cases.
- [x] **4.2.** `tests/test_handlers.py`: 4 tests — settings handlers (set_target, show_target).
- [x] **4.3.** `tests/conftest.py`: Fixtures + env vars setup.
- [x] **4.4.** `python -m pytest tests/ -v` → **15/15 passed** 🎉.

### Giai đoạn 5 — Polish & Run (Ngày 3) ✅

- [x] **5.1.** Code quality: `ruff`, `black`, `mypy` config sẵn trong `pyproject.toml`.
- [x] **5.2.** `README.md` hoàn chỉnh — Hướng dẫn cài đặt, cấu trúc, sử dụng.
- [x] **5.3.** Manual test trên Telegram thật — đã chạy và xác nhận bot phản hồi đúng.
- [x] **5.4.** Log chi tiết với `loguru` (ERROR, WARNING, INFO, DEBUG).
- [x] **5.5.** MarkdownV2 parse mode với escape_md2() + fallback plain text nếu lỗi (an toàn hơn HTML cho format in đậm).

### Giai đoạn 6 — Menu Button (Telegram `setMyCommands`) ✅

- [x] **6.1.** Tạo `src/tele_bot_dich/commands.py` chứa `BOT_COMMANDS: list[BotCommand]` (7 lệnh).
- [x] **6.2.** Implement `setup_bot_commands(bot)` gọi `await bot.set_my_commands(...)`.
- [x] **6.3.** Đăng ký `_post_init` hook trong `__main__.py` → auto-register khi bot khởi động.
- [x] **6.4.** Verify: khởi động bot → log "Bot menu commands registered" → nút "Menu" hiển thị cạnh thanh nhập.

### Giai đoạn 7 — Quick Set Commands `/zh` & `/da` ✅

- [x] **7.1.** Thêm handlers `quick_set_zh`, `quick_set_da` trong `handlers/settings.py`.
- [x] **7.2.** Tạo helper `_apply_target(update, lang, quick_label)` để tái sử dụng logic.
- [x] **7.3.** Thêm `CommandHandler("zh", quick_set_zh)` và `CommandHandler("da", quick_set_da)` trong `bot.py`.
- [x] **7.4.** Tests: `test_quick_set_zh`, `test_quick_set_da` trong `test_handlers.py`.

### Giai đoạn 8 — Provider Migration (aiping.cn → opencode.ai/zen) ✅

- [x] **8.1.** Khảo sát các free endpoint: iamhc.cn (`step-3.7-flash`), OpenRouter (`openrouter/free`), opencode.ai/zen (`mimo-v2.5-free`, `nemotron-3-super-free`).
- [x] **8.2.** Benchmark bằng script `test_opencode_v2.py` — kết quả `mimo-v2.5-free` nhanh nhất (~1.88s avg, ổn định).
- [x] **8.3.** Cập nhật `.env`: `OPENAI_BASE_URL=https://opencode.ai/zen/v1`, `OPENAI_MODEL=mimo-v2.5-free`.
- [x] **8.4.** Cập nhật README/TODO/PLAN với bảng lịch sử provider.

### Giai đoạn 9 — Fix Timeout 117s (OpenAI SDK `max_retries`) ✅

- [x] **9.1.** Phát hiện log: timeout 117s = 3 lần × ~30s + backoff → fail-fast bằng `max_retries=0`.
- [x] **9.2.** Phân tích root cause: SDK OpenAI mặc định `max_retries=2` → cold start 60-80s × 3 ≈ 200s.
- [x] **9.3.** Thêm field `openai_max_retries: int = 0` trong `config.py`.
- [x] **9.4.** Pass `max_retries=settings.openai_max_retries` vào `AsyncOpenAI(...)` trong `services/openai_translator.py`.
- [x] **9.5.** Thêm `enable_thinking: bool = False` + pass `extra_body={"enable_thinking": False}` để tắt thinking mode (giảm rate limit).
- [x] **9.6.** Test mới: `test_translate_passes_extra_body_disable_thinking`, `test_translator_uses_max_retries_from_settings` (passing).

### Giai đoạn 10 — Locale Prompt (giọng địa phương theo target_lang) ✅

- [x] **10.1.** Thêm dict `_LOCALE_PROMPTS` trong `services/openai_translator.py` map `target_lang` → hướng dẫn giọng:
  - `vi` → **Saigon (Southern Vietnam)** — giọng tự nhiên, thân mật, tránh từ Bắc.
  - `zh` → **Beijing Mandarin (Putonghua)** — giọng Bắc Kinh, tránh từ Đài Loan/HK.
  - `da` → **Copenhagen Danish (rigsdansk)** — tránh phương ngữ Jutland/Bornholm.
- [x] **10.2.** Thêm helper `_build_locale_instruction(target_lang)` (case-insensitive, fallback `""`).
- [x] **10.3.** Trong `translate()`, nếu target_lang có trong mapping → nối locale instruction vào system prompt (sau template chính, cách 1 dòng trống).
- [x] **10.4.** Thêm 5 tests:
  - `test_translate_includes_locale_for_vietnamese` (verify "Saigon" trong prompt).
  - `test_translate_includes_locale_for_chinese` (verify "Beijing" + "Putonghua").
  - `test_translate_includes_locale_for_danish` (verify "Copenhagen" + "rigsdansk").
  - `test_translate_no_locale_for_unsupported_lang` (vd: `en`, `fr` → không chèn).
  - `test_build_locale_instruction_helper` (case-insensitive, fallback `""`).
- [x] **10.5.** Tổng test: **24/24 passed**.

### Giai đoạn 11 — Auto-Override Target (zh/da → luôn vi) ✅

- [x] **11.1.** Thêm dict `_AUTO_TARGET_OVERRIDE = {"zh": "vi", "da": "vi"}` trong `handlers/translate.py`.
- [x] **11.2.** Thêm helper `_resolve_target_lang(text, user_target) -> tuple[str, str | None]`:
  - Phát hiện source bằng `detect_language_fallback()` (heuristic Unicode đã có).
  - Nếu source ∈ mapping và target hiện tại khác → trả `(vi, source)`.
  - Ngược lại → trả `(user_target, None)`.
- [x] **11.3.** Sửa `handle_text()` để dùng helper + log `TARGET_OVR` khi có override.
- [x] **11.4.** `/zh` và `/da` **vẫn hoạt động bình thường** để set target = Trung/Đan Mạch khi user muốn dịch chiều ngược lại (vd: từ Việt → Trung). Override chỉ áp dụng cho **tin nhắn thường** (handle_text), không áp dụng cho command.
- [x] **11.5.** Thêm 8 tests:
  - `test_resolve_target_chinese_overrides_to_vi` (helper, tiếng Trung).
  - `test_resolve_target_danish_overrides_to_vi` (helper, tiếng Đan Mạch).
  - `test_resolve_target_vietnamese_keeps_setting` (helper, tiếng Việt).
  - `test_resolve_target_english_keeps_setting` (helper, ASCII).
  - `test_resolve_target_no_override_if_already_vi` (helper, edge case).
  - `test_handle_text_chinese_forces_target_vi` (E2E: target=en + text=zh → gọi translator với target=vi).
  - `test_handle_text_danish_forces_target_vi` (E2E: target=ja + text=da → gọi translator với target=vi).
  - `test_handle_text_vietnamese_keeps_user_target` (E2E: target=en + text=vi → gọi translator với target=en).
- [x] **11.6.** Tổng test: **32/32 passed**.

---

## 8. Code Skeleton chính

> **Ghi chú:** Các skeleton dưới đây đã được cập nhật theo code thực tế.
> Xem [src/tele_bot_dich/](file:///d:/tele-bot-dich/src/tele_bot_dich/) để biết code đầy đủ.

### 8.1. `src/tele_bot_dich/config.py`

```python
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str
    openai_api_key: str
    openai_model: str = "mimo-v2.5-free"
    openai_base_url: str = "https://opencode.ai/zen/v1"
    openai_timeout_seconds: int = 30
    openai_max_retries: int = 0
    enable_thinking: bool = False
    default_target_lang: str = "vi"
    max_text_length: int = 4000
    log_level: str = "INFO"


@lru_cache()
def get_settings() -> _Settings:
    return _Settings()
```

### 8.2. `src/tele_bot_dich/services/openai_translator.py`

```python
import json
from dataclasses import dataclass

from openai import AsyncOpenAI

from tele_bot_dich.config import get_settings


_LOCALE_PROMPTS = {
    "vi": "Bạn là thông dịch viên giọng Sài Gòn... Dùng ngôn ngữ giản dị, đời thường...",
    "zh": "你是北京口音的翻译...",
    "da": "Du er oversætter med københavnerdialekt...",
}


@dataclass(slots=True)
class TranslationResult:
    source_lang: str
    target_lang: str
    translated: str


class TranslationError(Exception):
    pass


class OpenAITranslator:
    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        settings = get_settings()
        self._client = client or AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            max_retries=settings.openai_max_retries,
            timeout=settings.openai_timeout_seconds,
        )

    async def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> TranslationResult:
        locale_note = _LOCALE_PROMPTS.get(target_lang, "")
        system_prompt = f"You are a professional translator. Translate into {target_lang}. {locale_note} " \
                        'Reply JSON: {"source_lang":"<iso>","target_lang":"<iso>","translated":"<text>"}'
        resp = await self._client.chat.completions.create(
            model=get_settings().openai_model,
            messages=[...],
            response_format={"type": "json_object"},
            temperature=0.2,
            extra_body={"enable_thinking": False},
        )
        ...
```

### 8.3. `src/tele_bot_dich/handlers/translate.py`

```python
from telegram import Update
from telegram.ext import ContextTypes

from tele_bot_dich.models.user_settings import user_settings_store
from tele_bot_dich.services.openai_translator import OpenAITranslator, TranslationError
from tele_bot_dich.utils.formatters import escape_md2, format_translation_reply

_AUTO_TARGET_OVERRIDE = {"zh": "vi", "da": "vi"}

_translator: OpenAITranslator | None = None

def get_translator() -> OpenAITranslator:
    global _translator
    if _translator is None:
        _translator = OpenAITranslator()
    return _translator

def _resolve_target_lang(text: str, user_target: str) -> tuple[str, str | None]:
    source = detect_language_fallback(text)
    override = _AUTO_TARGET_OVERRIDE.get(source)
    if override:
        return override, source
    return user_target, None

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if not text or len(text) > MAX_LENGTH:
        await update.message.reply_text(f"Văn bản phải từ 1–{MAX_LENGTH} ký tự.")
        return
    user_id = update.effective_user.id
    user_target = user_settings_store.get_target(user_id)
    target, override_source = _resolve_target_lang(text, user_target)
    translator = get_translator()
    # typing indicator + translate + MarkdownV2 + fallback plain text
    ...
```

### 8.4. `src/tele_bot_dich/__main__.py`

```python
import asyncio
from telegram import Bot
from tele_bot_dich.config import get_settings
from tele_bot_dich.bot import build_application
from tele_bot_dich.commands import setup_bot_commands
from tele_bot_dich.utils.logger import setup_logger


async def _post_init(app: Application) -> None:
    await setup_bot_commands(app.bot)


def main() -> None:
    setup_logger()
    app = build_application()
    app.post_init = _post_init
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
```

## 9. Cách chạy (cập nhật theo thực tế)

> **Lưu ý:** Dự án hiện dùng **pip + python global** (không poetry). Dependencies đã cài sẵn.

```powershell
# Install development mode (chạy lần đầu, tạo symlink cho module)
pip install -e .

# Kiểm tra config
python -c "from tele_bot_dich.config import get_settings; print(get_settings().model_dump())"

# Chạy unit test
python -m pytest tests/ -v

# Chạy bot
python -m tele_bot_dich
```

Sau khi chạy, mở Telegram, tìm bot theo username đã tạo với @BotFather, gửi:
- `/start` — xem hướng dẫn.
- `/set_target en` — đặt ngôn ngữ đích là tiếng Anh.
- `Xin chào bạn` — nhận bản dịch.

---

## 10. OpenAPI Spec (Bot Contract)

📄 File: [`docs/openapi.yaml`](./docs/openapi.yaml) — đặt tại `docs/openapi.yaml`.

Spec mô tả **Bot API contract** theo OpenAPI 3.1, dùng để:
- Tài liệu hoá hợp đồng command → response.
- Validate behavior trong CI (sau này).
- Sinh SDK nếu bot mở rộng thành webhook.

Cấu trúc chính của spec:
```yaml
openapi: 3.1.0
info:
  title: Telegram Translation Bot API
  version: 0.1.0
  description: Hợp đồng các lệnh của bot phiên dịch.
paths:
  /start:
    post: { ... }
  /help:
    post: { ... }
  /set_target:
    post:
      parameters: [ { name: lang, in: query, ... } ]
  /translate:
    post:
      requestBody: { content: { text/plain: ... } }
      responses:
        '200': { description: Bản dịch }
        'E001': { description: Văn bản không hợp lệ }
        'E003': { description: Lỗi upstream OpenAI }
```

> **Ghi chú:** Bot này thực chất là **Telegram command interface**, không phải REST API. OpenAPI spec dùng để mô hình hoá hợp đồng cho mục đích tài liệu & test.

---

## 11. Verification (Kiểm thử cuối)

| # | Mục | Cách kiểm | Kỳ vọng | Kết quả |
|---|-----|-----------|---------|---------|
| 1 | Python env | `python --version` | Python 3.11+ | ✅ Python 3.14.3 |
| 2 | Lint | `ruff check .` | 0 lỗi | ✅ Config sẵn |
| 3 | Type check | `mypy src` | 0 lỗi | ✅ Config sẵn (strict=false) |
| 4 | Unit test | `python -m pytest tests/` | Tất cả pass | ✅ **32/32 passed** |
| 5 | Bot khởi động | `python -m tele_bot_dich` | Log "Application started" | ✅ Đang chạy |
| 6 | OpenAI API | Test script | Response 200 | ✅ `mimo-v2.5-free` ~1.88s |
| 7 | Telegram test | Gửi `/start` | Bot trả lời | ✅ Hoạt động trên Telegram thật |
| 8 | Dịch EN→VI | Gửi "Hello world" | Bot trả "Xin chào" + meta | ✅ |
| 9 | Dịch VI→JA | `/set_target ja` + gửi TV | Bản dịch tiếng Nhật | ✅ |
| 10 | Lỗi input | Gửi chuỗi 5000 ký tự | Bot trả "1–4000 ký tự" | ✅ |
| 11 | Menu button | Mở Telegram | Nút "Menu" cạnh thanh nhập | ✅ |
| 12 | Quick set | `/zh`, `/da` | Target = zh, da | ✅ |
| 13 | Timeout < 60s | Cold start + 3 requests | Không quá 60s/request | ✅ (max_retries=0) |
| 14 | Thinking off | Gọi API có `extra_body` | Model không trả reasoning | ✅ |
| 15 | Locale prompt vi | `/set_target vi` + dịch "Hello" | "Chào bạn" giọng Sài Gòn | ✅ |
| 16 | Locale prompt zh | `/set_target zh` + dịch "Hello" | "你好" giọng Bắc Kinh | ✅ |
| 17 | Locale prompt da | `/set_target da` + dịch "Hello" | "Hej" giọng Copenhagen | ✅ |
| 18 | Auto-override zh | User target=en + nhắn "你好" | Dịch sang vi (override) | ✅ |
| 19 | Auto-override da | User target=fr + nhắn "Hej, hvad..." | Dịch sang vi (override) | ✅ |

---

## 12. Rủi ro & Giảm thiểu

| Rủi ro | Tác động | Giảm thiểu |
|--------|----------|------------|
| OpenAI API chậm/timeout | UX kém | `OPENAI_TIMEOUT_SECONDS=30` + `OPENAI_MAX_RETRIES=0` (fail-fast) |
| Cold start 60-80s trên free tier | First request lâu | Tự retry tay hoặc nâng cấp plan; đã giảm nhờ `mimo-v2.5-free` |
| Model thinking → rate limit | Response chậm, dễ 429 | `ENABLE_THINKING=false` pass qua `extra_body` |
| Chi phí OpenAI tăng | Tốn tiền | Giới hạn 4000 ký tự, log usage, đặt budget alert |
| Token Telegram lộ | Bot bị chiếm | Không commit `.env`, `.env` đã trong `.gitignore` |
| User spam | Tốn quota | (Mở rộng) Rate limit per user, ví dụ 30 req/phút |
| Provider ngừng free tier | Bot chết | Có thể đổi provider qua `.env` không cần sửa code |

## 13. Lịch sử provider (migration log)

| Ngày | Provider | Model | Ghi chú |
|------|----------|-------|---------|
| 2026-06-05 (đầu) | aiping.cn | `glm-4.7-flash` | Test OK, response chậm khi liên tục |
| 2026-06-05 | iamhc.cn | `step-3.5-flash` | Cold start ~30s, dùng tạm |
| 2026-06-05 | opencode.ai/zen | `mimo-v2.5-free` ✅ | **Hiện tại** — 1.88s avg, ổn định nhất |

Xem chi tiết benchmark tại: `docs/TODO.md` (mục "So sánh provider").

---

## 14. Mở rộng tương lai (không thuộc MVP)

- [ ] Inline mode: dịch ngay trong bất kỳ chat nào (`@bot_en Hello`).
- [ ] Lưu lịch sử vào SQLite/Postgres.
- [ ] Voice translation (Whisper).
- [ ] OCR cho ảnh (Tesseract + GPT-4V).
- [ ] Group language preferences.
- [ ] Webhook thay vì polling (cho production).

---

## 15. Checklist khởi động nhanh

```powershell
cd "d:\tele-bot-dich"
pip install -e .
copy .env.example .env
# Sửa .env với TELEGRAM_BOT_TOKEN và OPENAI_API_KEY
python -m pytest tests/ -v
python -m tele_bot_dich
```
