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


# Цены Claude Sonnet 4.5 (на 2026-04, $/MTok)
PRICE_INPUT_PER_MTOK = 3.0
PRICE_OUTPUT_PER_MTOK = 15.0
DEFAULT_MODEL = "claude-sonnet-4-5"


class ClaudeService:
    """Высокоуровневая обёртка над Anthropic API для пайплайна."""

    def __init__(self, model: str = DEFAULT_MODEL, prompts_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.model = model
        self.prompts_dir = prompts_dir or self.settings.prompts_dir
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
        """Простой вызов Claude API. Возвращает текст ответа."""
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

                response = self.client.messages.create(**kwargs)

                # Учёт токенов
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens
                self.total_calls += 1

                # Извлекаем текст
                text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text += block.text
                return text

            except AnthropicAPIError as e:
                last_error = e
                wait = 2 ** attempt
                log.warning(f"Claude API ошибка (попытка {attempt+1}/{retries}): {e}. Жду {wait}с...")
                time.sleep(wait)

        raise APIError("Claude", f"Все попытки провалились: {last_error}")

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
