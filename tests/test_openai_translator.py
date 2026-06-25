"""Test OpenAITranslator với mock client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import APIConnectionError

from tele_bot_dich.services.openai_translator import (
    OpenAITranslator,
    TranslationError,
)


def _build_mock_client(content: str) -> MagicMock:
    """Tạo mock AsyncOpenAI client trả về content cho completion."""
    client = MagicMock()
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = content
    client.chat.completions.create = AsyncMock(return_value=completion)
    return client


@pytest.mark.asyncio
async def test_translate_parses_valid_json() -> None:
    payload = (
        '{"source_lang": "en", "target_lang": "vi", '
        '"translated": "Xin chào"}'
    )
    client = _build_mock_client(payload)
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    result = await translator.translate("Hello", target_lang="vi")

    assert result.source_lang == "en"
    assert result.target_lang == "vi"
    assert result.translated == "Xin chào"


@pytest.mark.asyncio
async def test_translate_uses_defaults_on_missing_keys() -> None:
    payload = json.dumps({"translated": "Xin chào"})
    client = _build_mock_client(payload)
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    result = await translator.translate("Hello", target_lang="vi", source_lang="en")

    assert result.source_lang == "en"  # fallback to param
    assert result.target_lang == "vi"
    assert result.translated == "Xin chào"


@pytest.mark.asyncio
async def test_translate_raises_on_invalid_json() -> None:
    client = _build_mock_client("not a json {")
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    with pytest.raises(TranslationError, match="Invalid JSON"):
        await translator.translate("Hello", target_lang="vi")


@pytest.mark.asyncio
async def test_translate_raises_on_empty_response() -> None:
    client = _build_mock_client("   ")
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    with pytest.raises(TranslationError, match="Empty response"):
        await translator.translate("Hello", target_lang="vi")


@pytest.mark.asyncio
async def test_translate_wraps_openai_errors() -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        side_effect=APIConnectionError(request=MagicMock()),
    )
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    with pytest.raises(TranslationError, match="Upstream OpenAI error"):
        await translator.translate("Hello", target_lang="vi")


@pytest.mark.asyncio
async def test_translate_rejects_empty_text() -> None:
    client = _build_mock_client('{"translated": ""}')
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    with pytest.raises(TranslationError, match="Empty text"):
        await translator.translate("   ", target_lang="vi")


@pytest.mark.asyncio
async def test_translate_passes_extra_body_disable_thinking() -> None:
    """Verify enable_thinking=False được pass qua extra_body."""
    client = _build_mock_client(
        '{"source_lang": "en", "target_lang": "vi", "translated": "Xin chào"}'
    )
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    await translator.translate("Hello", target_lang="vi")

    # Check that create was called with extra_body
    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert "extra_body" in call_kwargs
    assert call_kwargs["extra_body"]["enable_thinking"] is False


def test_translator_uses_max_retries_from_settings() -> None:
    """Verify max_retries=0 được pass cho AsyncOpenAI constructor (tránh retry ngầm)."""
    from unittest.mock import patch

    from tele_bot_dich.config import settings

    with patch("tele_bot_dich.services.openai_translator.AsyncOpenAI") as mock_cls:
        mock_cls.return_value = MagicMock()
        OpenAITranslator()  # tạo mới với default settings

        # Verify constructor được gọi với max_retries=0
        call_kwargs = mock_cls.call_args.kwargs
        assert "max_retries" in call_kwargs
        assert call_kwargs["max_retries"] == settings.openai_max_retries
        # Verify timeout cũng được pass
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == settings.openai_timeout_seconds


# === Locale prompt tests (giọng địa phương theo target_lang) ===


@pytest.mark.asyncio
async def test_translate_includes_locale_for_vietnamese() -> None:
    """Tiếng Việt → phải có hướng dẫn giọng Sài Gòn trong system prompt."""
    client = _build_mock_client(
        '{"source_lang": "en", "target_lang": "vi", "translated": "Chào bạn"}'
    )
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    await translator.translate("Hello", target_lang="vi")

    messages = client.chat.completions.create.call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]
    assert "Saigon" in system_prompt
    assert "Southern Vietnam" in system_prompt


@pytest.mark.asyncio
async def test_translate_includes_locale_for_chinese() -> None:
    """Tiếng Trung → phải có hướng dẫn giọng Bắc Kinh trong system prompt."""
    client = _build_mock_client(
        '{"source_lang": "en", "target_lang": "zh", "translated": "你好"}'
    )
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    await translator.translate("Hello", target_lang="zh")

    messages = client.chat.completions.create.call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]
    assert "Beijing" in system_prompt
    assert "Putonghua" in system_prompt


@pytest.mark.asyncio
async def test_translate_includes_locale_for_danish() -> None:
    """Tiếng Đan Mạch → phải có hướng dẫn giọng Copenhagen trong system prompt."""
    client = _build_mock_client(
        '{"source_lang": "en", "target_lang": "da", "translated": "Hej"}'
    )
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    await translator.translate("Hello", target_lang="da")

    messages = client.chat.completions.create.call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]
    assert "Copenhagen" in system_prompt
    assert "rigsdansk" in system_prompt


@pytest.mark.asyncio
async def test_translate_no_locale_for_unsupported_lang() -> None:
    """Ngôn ngữ không có trong mapping (vd: 'en', 'fr') → không chèn locale."""
    client = _build_mock_client(
        '{"source_lang": "vi", "target_lang": "en", "translated": "Hello"}'
    )
    translator = OpenAITranslator(client=client)  # type: ignore[arg-type]

    await translator.translate("Xin chào", target_lang="en")

    messages = client.chat.completions.create.call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]
    # System prompt chỉ chứa template gốc, không có region instruction
    assert "Saigon" not in system_prompt
    assert "Beijing" not in system_prompt
    assert "Copenhagen" not in system_prompt
    assert "Cantonese" not in system_prompt
    # Nhưng vẫn chứa JSON schema bắt buộc
    assert "source_lang" in system_prompt
    assert "translated" in system_prompt


def test_build_locale_instruction_helper() -> None:
    """Unit test helper `_build_locale_instruction`."""
    from tele_bot_dich.services.openai_translator import _build_locale_instruction

    # Có trong mapping
    assert "Saigon" in _build_locale_instruction("vi")
    assert "Beijing" in _build_locale_instruction("zh")
    assert "Copenhagen" in _build_locale_instruction("da")
    # Case-insensitive
    assert "Saigon" in _build_locale_instruction("VI")
    # Không có trong mapping → rỗng
    assert _build_locale_instruction("en") == ""
    assert _build_locale_instruction("fr") == ""
    assert _build_locale_instruction("") == ""
