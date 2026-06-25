"""OpenAI-based translation service.

Gọi OpenAI Chat Completions với response_format=json_object để ép output
JSON có cấu trúc: {source_lang, target_lang, translated}.

Có fallback:
- Nếu model trả source_lang='auto' (model không tuân thủ prompt) → dùng
  `language_detector.detect_language_fallback` (heuristic Unicode).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from tele_bot_dich.config import settings
from tele_bot_dich.services.language_detector import detect_language_fallback
from tele_bot_dich.utils.logger import logger


@dataclass(slots=True)
class TranslationResult:
    """Kết quả dịch trả về cho handler."""

    source_lang: str
    target_lang: str
    translated: str


class TranslationError(RuntimeError):
    """Lỗi khi gọi OpenAI hoặc parse output."""


_SYSTEM_PROMPT_TEMPLATE = (
    "You are a professional translator. "
    "Detect the source language of the user's text and translate it into {target_lang}. "
    'Reply strictly as a JSON object with this exact schema: '
    '{{"source_lang": "<iso_639_1_code>", '
    '"target_lang": "<iso_639_1_code>", '
    '"translated": "<translated_text>"}}. '
    "Do not add any commentary, code fences, or extra keys."
)

# Giọng/region cho từng target_lang phổ biến.
# Khi target_lang nằm trong dict này, một hướng dẫn giọng sẽ được nối vào
# system prompt để model dịch theo giọng địa phương cụ thể.
# Key: ISO 639-1 (lowercase); Value: mô tả giọng/region bằng tiếng Anh (model đọc).
_LOCALE_PROMPTS: dict[str, str] = {
    "vi": (
        "Use the Saigon (Southern Vietnam) dialect of Vietnamese: "
        "natural, friendly, casual register. Prefer Southern vocabulary "
        "and common Saigon expressions when appropriate (vd: informal 'tao/mày' "
        "vs 'tôi/bạn'). Avoid Northern Hanoi-specific slang."
    ),
    "zh": (
        "Use Standard Mandarin (Putonghua) with a Northern/Beijing "
        "accent and register: natural, conversational tone, common "
        "Beijing expressions and modern Mainland China vocabulary. "
        "Avoid Taiwan-specific terms (zh-TW) and Cantonese/Hong Kong slang."
    ),
    "da": (
        "Use standard Danish (rigsdansk) with a Copenhagen "
        "(København) accent and register: natural, modern, everyday "
        "Copenhagen speech patterns. Avoid regional dialects "
        "(Jutlandic/jysk, Bornholmsk) and overly formal or archaic Danish."
    ),
}


def _build_locale_instruction(target_lang: str) -> str:
    """Trả về hướng dẫn giọng địa phương cho `target_lang`, hoặc chuỗi rỗng.

    Args:
        target_lang: Mã ngôn ngữ ISO 639-1 (case-insensitive).

    Returns:
        Câu hướng dẫn giọng/region, hoặc "" nếu không có trong `_LOCALE_PROMPTS`.
    """
    return _LOCALE_PROMPTS.get(target_lang.strip().lower(), "")


class OpenAITranslator:
    """Service dịch văn bản dùng OpenAI.

    Args:
        client: Optional AsyncOpenAI client (dùng để inject mock trong test).
            Nếu None, sẽ tự tạo từ settings.
    """

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
            # Tắt retry tự động: nếu timeout, fail ngay để user biết
            # (default SDK = 2 retries → timeout 30s × 3 = 90s + backoff = ~117s)
            max_retries=settings.openai_max_retries,
        )

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
    ) -> TranslationResult:
        """Dịch `text` sang `target_lang`.

        Args:
            text: Văn bản cần dịch (đã trim, đã validate độ dài).
            target_lang: Mã ngôn ngữ đích ISO 639-1 (vd: 'vi', 'en').
            source_lang: Mã ngôn ngữ nguồn hoặc 'auto' để GPT tự phát hiện.

        Returns:
            TranslationResult với 3 trường: source/target lang code + bản dịch.

        Raises:
            TranslationError: Khi OpenAI lỗi hoặc output không parse được JSON.
        """
        if not text.strip():
            raise TranslationError("Empty text")

        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(target_lang=target_lang)

        # Nối hướng dẫn giọng địa phương nếu target_lang có trong mapping.
        # Ví dụ: 'vi' → giọng Sài Gòn, 'zh' → giọng Bắc Kinh, 'da' → giọng Copenhagen.
        locale_instruction = _build_locale_instruction(target_lang)
        if locale_instruction:
            system_prompt = f"{system_prompt}\n\n{locale_instruction}"
            logger.debug(
                "Applied locale instruction for target_lang={}: {} chars",
                target_lang,
                len(locale_instruction),
            )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        if source_lang != "auto":
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"The source language is {source_lang}. Do not translate "
                        "from any other language."
                    ),
                }
            )
        messages.append({"role": "user", "content": text})

        try:
            # extra_body cho phép pass provider-specific options mà OpenAI SDK
            # không expose (vd: enable_thinking của GLM-4.7, Qwen3, ...).
            # Tắt thinking giúp giảm rate limit + phản hồi nhanh hơn.
            extra_body: dict[str, Any] = {"enable_thinking": settings.enable_thinking}
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,  # type: ignore[arg-type]
                response_format={"type": "json_object"},
                temperature=0.2,
                extra_body=extra_body,
            )
        except OpenAIError as exc:
            logger.error("OpenAI API error: {}", exc)
            raise TranslationError(f"Upstream OpenAI error: {exc}") from exc

        raw: str = (response.choices[0].message.content or "").strip()
        if not raw:
            raise TranslationError("Empty response from OpenAI")

        # Một số model (vd OpenRouter routing) trả control characters
        # trong JSON — strip chúng trước khi parse.
        raw = raw.replace("\x00", "").replace("\x0b", "").replace("\x0c", "")
        # Nếu model trộn markdown ```json ... ``` thì strip.
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            data: dict[str, Any] = json.loads(raw, strict=False)
        except json.JSONDecodeError as exc:
            logger.error("Cannot parse OpenAI JSON: {}", raw[:300])
            raise TranslationError(f"Invalid JSON from OpenAI: {exc}") from exc

        # Lấy source_lang từ model; nếu model trả 'auto' (không tuân thủ prompt)
        # thì dùng heuristic fallback để có mã cụ thể hơn.
        model_source = str(data.get("source_lang") or "auto").strip().lower()
        if not model_source or model_source == "auto":
            detected = detect_language_fallback(text)
            if detected != "auto":
                model_source = detected
            else:
                model_source = source_lang if source_lang != "auto" else "auto"

        # Lấy bản dịch
        translated_text = str(data.get("translated") or "").strip()

        # Fallback: nếu model không trả translated mà trả field khác (vd 'text', 'translation')
        if not translated_text:
            for alt_key in ("text", "translation", "result", "output"):
                alt_value = data.get(alt_key)
                if alt_value and isinstance(alt_value, str):
                    translated_text = alt_value.strip()
                    logger.warning("Used fallback field '{}' for translated", alt_key)
                    break

        return TranslationResult(
            source_lang=model_source,
            target_lang=str(data.get("target_lang") or target_lang),
            translated=translated_text,
        )


__all__ = [
    "OpenAITranslator",
    "TranslationError",
    "TranslationResult",
    "_LOCALE_PROMPTS",
    "_build_locale_instruction",
]
