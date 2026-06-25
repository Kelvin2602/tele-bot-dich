# 📋 TODO - Lịch sử UI/UX + Tính năng mới

> **Ngày tạo:** 2026-06-05
> **Cập nhật cuối:** 2026-06-25
> **Trạng thái:** ✅ Đã thêm Menu button + Quick commands + Fix timeout + Locale prompt + **Auto-override target**

---

## 🆕 Tính năng mới 2026-06-05 (sau reset)

### 1. Menu button (setMyCommands)

Telegram tự hiển thị nút **Menu** cạnh thanh nhập tin nhắn chứa 7 lệnh.

**File mới:** `src/tele_bot_dich/commands.py`
- `BOT_COMMANDS`: list 7 BotCommand
- `setup_bot_commands(bot)`: gọi `set_my_commands` qua Telegram API

**File sửa:**
- `__main__.py`: `app.post_init = _post_init` hook
- `bot.py`: đăng ký 7 CommandHandler
- `handlers/start.py`: WELCOME/HELP update

### 2. `/settings` command mới

Hiển thị cấu hình + 10 ngôn ngữ phổ biến + quick set hints.

```
⚙️ Cài đặt

🌐 Ngôn ngữ đích hiện tại: vi

Đổi ngôn ngữ đích:
Gõ /set_target <mã> với mã ISO 639-1 bất kỳ.
Ví dụ: /set_target en

Quick set: /zh (Trung) · /da (Đan Mạch)

Một số mã phổ biến:
  • vi — Tiếng Việt ✓
  • en — English
  • zh — 中文
  • ja — 日本語
  ...
```

### 3. Quick set commands `/zh` và `/da`

| Command | Target | Reply |
|---------|--------|-------|
| `/zh` | `zh` (Tiếng Trung) | `✅ Đã đặt ngôn ngữ đích: zh` |
| `/da` | `da` (Tiếng Đan Mạch) | `✅ Đã đặt ngôn ngữ đích: da` |

**File sửa:**
- `handlers/settings.py`: thêm `_apply_target()` helper + `quick_set_zh()` + `quick_set_da()`
- `bot.py`: `CommandHandler("zh")` + `CommandHandler("da")`
- `commands.py`: thêm vào Menu
- `tests/test_handlers.py`: 2 test mới

### 4. Provider migration: aiping.cn → opencode.ai/zen

**Lý do:** aiping.cn + GLM-4.7-Flash có cold start timeout 60-117s. opencode.ai/zen + mimo-v2.5-free chỉ mất ~1.88s.

| Provider | Cold start | Warm avg | Reliability |
|----------|-----------|----------|-------------|
| aiping.cn (cũ) | 60-117s | 3-15s | 8/8 OK |
| **opencode.ai/zen mimo** ⚡ | **~1.5s** | **1.88s** | **8/8 OK** |

**File sửa:**
- `.env`: đổi `OPENAI_BASE_URL`, `OPENAI_MODEL`
- `config.py`: thêm `openai_max_retries: int = 0` (fix timeout 117s)
- `services/openai_translator.py`: pass `max_retries=0` cho AsyncOpenAI

### 5. Fix timeout 117s

**Nguyên nhân:** OpenAI SDK mặc định `max_retries=2` → 3 lần × 30s + backoff = ~117s.

**Fix:**
- `OPENAI_MAX_RETRIES=0` (fail-fast)
- `OPENAI_TIMEOUT_SECONDS=60` (cold start buffer)
- Typing indicator refresh mỗi 4s (UX tốt hơn)
- Error message hiển thị elapsed time

### 6. Locale prompt — giọng địa phương theo target_lang

**Mục đích:** Khi dịch sang `vi`/`zh`/`da`, model được nhắc dùng giọng địa phương cụ thể
thay vì giọng "generic".

| target_lang | Locale / giọng | Tránh |
|-------------|---------------|-------|
| `vi` | **Saigon (Southern Vietnam)** — tự nhiên, thân mật, từ vựng miền Nam | Từ Bắc, slang Hà Nội |
| `zh` | **Beijing Mandarin (Putonghua)** — giọng Bắc Kinh, hiện đại | Từ Đài Loan, Cantonese |
| `da` | **Copenhagen Danish (rigsdansk)** — hiện đại, tự nhiên | Phương ngữ Jutland, Bornholm |

**File sửa:**
- `services/openai_translator.py`:
  - Thêm dict `_LOCALE_PROMPTS` (key: ISO 639-1, value: mô tả giọng tiếng Anh)
  - Thêm helper `_build_locale_instruction(target_lang)` (case-insensitive)
  - Trong `translate()`, nối locale instruction vào system prompt nếu target_lang có trong mapping
- `tests/test_openai_translator.py`: thêm 5 tests (vi/zh/da/unsupported/helper)

**Cách hoạt động:**

```python
# Target = "vi" → system prompt sẽ là:
# "...translate it into vi. Reply strictly as JSON..."
# (template gốc)
#
# + "\n\n"
# + "Use the Saigon (Southern Vietnam) dialect of Vietnamese: ..."
# (locale instruction)
```

**Không ảnh hưởng các ngôn ngữ khác** (vd: `en`, `fr`, `ja`, `ko`) — nếu target_lang
không có trong `_LOCALE_PROMPTS`, system prompt giữ nguyên template gốc.

### 7. Auto-Override Target — zh/da → luôn dịch sang vi

**Vấn đề:** Trước đây, khi user đã `/set_target en` rồi nhắn tiếng Trung hoặc
tiếng Đan Mạch, bot vẫn dịch sang tiếng Anh. Không đúng ý đồ — user muốn
dịch sang tiếng Việt.

**Giải pháp:** Trước khi gọi translator, kiểm tra source language bằng
heuristic Unicode. Nếu source ∈ {`zh`, `da`} → tự động override target = `vi`
(bất kể user setting hiện tại).

**`/zh` và `/da` vẫn hoạt động bình thường** — chúng set target = Trung/Đan Mạch
khi user muốn dịch chiều ngược lại (vd: từ Việt → Trung). Override chỉ áp dụng
cho **tin nhắn thường** (handle_text), không áp dụng cho command.

| User target | User nhắn | Translator được gọi với | Bản dịch |
|-------------|----------|------------------------|----------|
| `en` | "你好世界" | `target_lang=vi` | "Xin chào thế giới" |
| `fr` | "Hej, hvad laver du" | `target_lang=vi` | "Xin chào, bạn đang làm gì" |
| `ja` | "你好朋友" | `target_lang=vi` | "Xin chào bạn" |
| `en` | "Xin chào bạn" | `target_lang=en` | "Hello friend" (giữ setting) |
| `vi` | "Hello world" | `target_lang=vi` | "Xin chào thế giới" (giữ setting) |

**File sửa:**
- `handlers/translate.py`:
  - Thêm dict `_AUTO_TARGET_OVERRIDE = {"zh": "vi", "da": "vi"}`
  - Thêm helper `_resolve_target_lang(text, user_target) -> tuple[str, str | None]`
  - Sửa `handle_text()` để dùng helper + log `TARGET_OVR` khi có override
- `tests/test_handlers.py`: thêm 8 tests (5 helper + 3 E2E)

**Log format mới:**

```
TARGET_OVR user=12345 src=zh old=en → new=vi (luôn dịch sang Việt)
RECV    user=12345 (@tester) target=vi text='你好世界...'
```

---

## 🔄 Reset ngày 2026-06-05 (sớm hơn)

Theo yêu cầu user: **xoá hết tất cả nút button inline + chức năng callback**.

### Đã xoá

| Hạng mục | Trước | Sau |
|----------|-------|-----|
| File `keyboards.py` | ✅ Có | ❌ Đã xoá |
| `InlineKeyboardMarkup` trong `/help` | ✅ Có (9 nút) | ❌ Xoá |
| `CallbackQueryHandler` trong `bot.py` | ✅ Đăng ký | ❌ Xoá |
| `on_set_lang_callback` trong `settings.py` | ✅ Có | ❌ Xoá |
| `on_callback_query` trong `settings.py` | ✅ Có | ❌ Xoá |
| `_on_help_check`, `_on_help_settings`, `_on_start_callback` | ✅ Có | ❌ Xoá |

### Kết quả sau reset → sau khi thêm tính năng mới → sau locale prompt → sau auto-override

| Hạng mục | Sau reset | Sau thêm mới | Sau locale prompt | Sau auto-override |
|----------|-----------|--------------|-------------------|-------------------|
| **Tổng handlers** | 6 (4 command + 2 message) | **8** (5 command + 1 message + 1 typing + 1 unsupported) | 8 (giữ nguyên) | 8 (giữ nguyên) |
| **InlineKeyboard / ReplyKeyboard** | 0 | 0 | 0 | 0 |
| **Callback handler** | 0 | 0 | 0 | 0 |
| **Slash commands** | 4 | **7** | 7 (giữ nguyên) | 7 (giữ nguyên) |
| **Tests** | 15/15 PASS | **19/19 PASS** | **24/24 PASS** | **32/32 PASS** |
| **Provider** | iamhc.cn | **opencode.ai/zen** | opencode.ai/zen | opencode.ai/zen |
| **Model** | step-3.5-flash | **mimo-v2.5-free** | mimo-v2.5-free | mimo-v2.5-free |
| **Locale prompt** | ❌ | ❌ | ✅ vi (Saigon) / zh (Beijing) / da (Copenhagen) | ✅ (giữ nguyên) |
| **Auto-override target** | ❌ | ❌ | ❌ | ✅ zh/da → luôn vi |

### Bot hiện tại làm được

| Lệnh | Chức năng |
|------|-----------|
| `/start` | Tin nhắn chào + liệt kê lệnh |
| `/help` | Hướng dẫn text-only (không nút) |
| `/settings` | Cài đặt + gợi ý 10 ngôn ngữ + quick set hints |
| `/target` | Xem ngôn ngữ đích hiện tại |
| `/set_target <code>` | Đặt ngôn ngữ đích |
| `/zh` | **Quick set:** dịch sang Tiếng Trung |
| `/da` | **Quick set:** dịch sang Tiếng Đan Mạch |
| Tin nhắn văn bản | Dịch sang target (kèm typing indicator) |
| Ảnh/voice/sticker | Hướng dẫn dùng text |

---

## 📜 Lịch sử (đã làm trước đó)

Xem [PLAN.md](../PLAN.md) để biết chi tiết quá trình phát triển.

---

## 🧹 Cleanup 2026-06-25

Dọn dẹp thư mục gốc — xoá 30+ file test/provider/log không còn dùng.

### Đã làm

- Tạo thư mục `_archive/` với 3 phân loại:
  - `_archive/scripts/` — 19 file benchmark & test thử nghiệm
  - `_archive/test_data/` — 6 file JSON test data
  - `_archive/logs/` — 8 file log cũ
- Thư mục gốc chỉ còn: `.env`, `pyproject.toml`, `README.md`, `PLAN.md`, `src/`, `tests/`, `docs/`, `_archive/`

### Kết quả cuối

| Hạng mục | Giá trị |
|----------|---------|
| **Tests** | **32/32 PASS** |
| **Provider** | opencode.ai/zen |
| **Model** | mimo-v2.5-free |
| **Locale prompt** | ✅ vi (Saigon) / zh (Beijing) / da (Copenhagen) |
| **Auto-override target** | ✅ zh/da → luôn vi |
| **Thư mục gốc** | Sạch — 8 thư mục/file chính |
