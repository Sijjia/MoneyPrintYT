"""
core/exceptions.py
Кастомные исключения пайплайна.
"""


class WebikPipelineError(Exception):
    """Базовое исключение пайплайна."""
    pass


class ConfigError(WebikPipelineError):
    """Ошибка конфигурации (отсутствует ключ и т.д.)."""
    pass


class StageError(WebikPipelineError):
    """Ошибка во время выполнения этапа."""

    def __init__(self, stage: int, message: str):
        self.stage = stage
        super().__init__(f"[Stage {stage}] {message}")


class APIError(WebikPipelineError):
    """Ошибка внешнего API."""

    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(f"[{service}] {message}")


class ValidationError(WebikPipelineError):
    """Невалидный JSON/структура от LLM."""
    pass
