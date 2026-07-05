"""
services/llm/claude.py
Обёртка над Anthropic Claude API.
Поддерживает:
- Загрузку промт-шаблонов из файлов
- Подстановку переменных через {{VAR}} синтаксис
- Парсинг JSON из ответа (с авто-исправлением markdown-блоков)
- Подсчёт стоимости запросов
- Retry при сбоях
"""
import json
import re
import time
from pathlib import Path
from typing import Any, Optional, Dict
from anthropic import Anthropic, APIError as AnthropicAPIError

from core.config import get_settings
from core.exceptions import APIError, ValidationError
from core.logger import setup_logger

log = setup_logger("claude")


# Цены Claude Sonnet 4.5 (на 2026-04, $/MTok). Для OpenRouter это лишь грубая
# оценка — реальная цена зависит от выбранной модели.
PRICE_INPUT_PER_MTOK = 3.0
PRICE_OUTPUT_PER_MTOK = 15.0
DEFAULT_MODEL = "claude-sonnet-4-5"
# Дефолтная модель при работе через OpenRouter (формат OpenRouter, не Anthropic).
DEFAULT_OPENROUTER_MODEL = "anthropic/claude-sonnet-4.5"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class ClaudeService:
    """Высокоуровневая обёртка над LLM для пайплайна.

    Два провайдера, выбор автоматический по .env:
    - OpenRouter (если задан OPENROUTER_API_KEY) — OpenAI-формат, любая модель
      через LLM_MODEL (напр. "anthropic/claude-sonnet-4.5", "google/gemini-2.5-flash").
    - Anthropic напрямую (иначе) — как раньше, ANTHROPIC_API_KEY.
    Публичный интерфейс одинаков для обоих.
    """

    def __init__(self, model: Optional[str] = None, prompts_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.prompts_dir = prompts_dir or self.settings.prompts_dir

        or_key = getattr(self.settings, "openrouter_api_key", None)
        if or_key:
            from openai import OpenAI
            self.provider = "openrouter"
            self.model = model or self.settings.llm_model or DEFAULT_OPENROUTER_MODEL
            self.client = OpenAI(api_key=or_key, base_url=OPENROUTER_BASE_URL)
        else:
            self.provider = "anthropic"
            self.model = model or DEFAULT_MODEL
            key = self.settings.anthropic_api_key
            if key.startswith("sk-ant-oat"):
                self.client = Anthropic(
                    auth_token=key,
                    default_headers={
                        "anthropic-beta": "oauth-2025-04-20",
                        "User-Agent": "claude-cli/1.0",
                    },
                )
            else:
                self.client = Anthropic(api_key=key)

        # Статистика
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0

    def load_prompt(self, name: str) -> str:
        """Загрузить промт-шаблон по имени (без расширения)."""
        prompt_path = self.prompts_dir / f"{name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Промт-шаблон не найден: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """Подставляет {{VAR}} переменные в шаблон."""
        result = template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            if isinstance(value, (dict, list)):
                str_value = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                str_value = str(value) if value is not None else ""
            result = result.replace(placeholder, str_value)
        return result

    def call(
        self,
        prompt: str,
        max_tokens: int = 16000,
        temperature: float = 1.0,
        system: Optional[str] = None,
        retries: int = 3,
    ) -> str:
        """Простой вызов LLM. Возвращает текст ответа."""
        if self.provider == "openrouter":
            return self._call_openrouter(prompt, max_tokens, temperature, system, retries)

        last_error = None

        for attempt in range(retries):
            try:
                kwargs = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system:
                    kwargs["system"] = system

                # Стриминг: SDK требует его для запросов, которые могут идти >10 мин
                # (большие max_tokens). Накапливаем текст и берём финальный usage.
                text = ""
                with self.client.messages.stream(**kwargs) as stream:
                    for chunk in stream.text_stream:
                        text += chunk
                    final = stream.get_final_message()

                # Учёт токенов
                self.total_input_tokens += final.usage.input_tokens
                self.total_output_tokens += final.usage.output_tokens
                self.total_calls += 1
                return text

            except AnthropicAPIError as e:
                last_error = e
                wait = 2 ** attempt
                log.warning(f"Claude API ошибка (попытка {attempt+1}/{retries}): {e}. Жду {wait}с...")
                time.sleep(wait)

        raise APIError("Claude", f"Все попытки провалились: {last_error}")

    def _call_openrouter(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system: Optional[str],
        retries: int,
    ) -> str:
        """Вызов через OpenRouter (OpenAI-формат). Стримим, чтобы не упереться
        в таймаут на больших max_tokens, и берём финальный usage."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for attempt in range(retries):
            try:
                text = ""
                usage = None
                stream = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    stream=True,
                    stream_options={"include_usage": True},
                )
                for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            text += delta.content
                    if getattr(chunk, "usage", None):
                        usage = chunk.usage

                if usage:
                    self.total_input_tokens += usage.prompt_tokens or 0
                    self.total_output_tokens += usage.completion_tokens or 0
                self.total_calls += 1
                if not text.strip():
                    raise ValidationError("OpenRouter вернул пустой ответ")
                return text

            except Exception as e:  # openai.* + сетевые
                last_error = e
                wait = 2 ** attempt
                log.warning(
                    f"OpenRouter ошибка (попытка {attempt+1}/{retries}, "
                    f"model={self.model}): {e}. Жду {wait}с..."
                )
                time.sleep(wait)

        raise APIError("OpenRouter", f"Все попытки провалились: {last_error}")

    def call_json(
        self,
        prompt: str,
        max_tokens: int = 16000,
        temperature: float = 1.0,
        system: Optional[str] = None,
        retries: int = 3,
    ) -> Any:
        """Вызывает Claude и парсит JSON из ответа.
        Автоматически удаляет ```json ... ``` обёртки если есть."""
        text = self.call(prompt, max_tokens, temperature, system, retries)
        return self._parse_json(text)

    @staticmethod
    def _parse_json(text: str) -> Any:
        """Извлекает JSON из ответа, удаляя markdown-блоки."""
        text = text.strip()

        # Убираем ```json ... ``` или ``` ... ```
        if text.startswith("```"):
            match = re.match(r"^```(?:json)?\s*\n(.*?)\n```\s*$", text, re.DOTALL)
            if match:
                text = match.group(1)
            else:
                # Просто отрезаем первую и последнюю строки если ``` есть
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines)

        # Иногда модель добавляет текст до/после JSON
        # Находим первый { или [ и последний } или ]
        start_obj = text.find("{")
        start_arr = text.find("[")
        if start_obj == -1 and start_arr == -1:
            raise ValidationError(f"В ответе не найден JSON: {text[:200]}")

        if start_obj == -1:
            start = start_arr
            end_char = "]"
        elif start_arr == -1:
            start = start_obj
            end_char = "}"
        else:
            start = min(start_obj, start_arr)
            end_char = "}" if start == start_obj else "]"

        end = text.rfind(end_char)
        if end == -1 or end < start:
            raise ValidationError(f"Не нашёл конец JSON в ответе")

        json_text = text[start:end + 1]

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            log.error(f"JSON parse error: {e}\n--- Исходный текст ---\n{json_text[:1000]}\n---")
            raise ValidationError(f"Невалидный JSON от Claude: {e}")

    def estimate_cost(self) -> float:
        """Стоимость в долларах от запросов в этой сессии."""
        cost = (self.total_input_tokens / 1_000_000) * PRICE_INPUT_PER_MTOK
        cost += (self.total_output_tokens / 1_000_000) * PRICE_OUTPUT_PER_MTOK
        return round(cost, 4)

    def stats(self) -> dict:
        return {
            "calls": self.total_calls,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "cost_usd": self.estimate_cost(),
        }
