"""
core/telegram_bot.py
Telegram-бот для уведомлений и команд.

Поддерживает:
- /status — статус всех проектов
- /projects — список проектов
- /approve <project> — одобрить чекпоинт
- /revise <project> <feedback> — переделать с фидбеком
- /regen <project> — перегенерировать без фидбека

Также шлёт уведомления когда этап готов.

Запуск: python -m core.telegram_bot
"""
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, CallbackQueryHandler,
)

from core.config import get_settings
from core.logger import setup_logger
from core.state import StateManager, Stage, StageStatus

log = setup_logger("telegram")


class WebikTelegramBot:
    """Бот для управления пайплайном из Telegram."""

    def __init__(self):
        self.settings = get_settings()
        if not self.settings.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env")

        self.app = Application.builder().token(self.settings.telegram_bot_token).build()
        self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("projects", self.cmd_projects))
        self.app.add_handler(CommandHandler("approve", self.cmd_approve))
        self.app.add_handler(CommandHandler("revise", self.cmd_revise))
        self.app.add_handler(CommandHandler("regen", self.cmd_regen))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await update.message.reply_text(
            f"🧊 Webik Pipeline Bot\n\n"
            f"Твой chat_id: `{chat_id}`\n"
            f"Скопируй его в .env как TELEGRAM_CHAT_ID\n\n"
            f"Команды: /help",
            parse_mode="Markdown",
        )

    async def cmd_help(self, update: Update, context):
        await update.message.reply_text(
            "Команды:\n"
            "/status — статус всех проектов\n"
            "/projects — список проектов\n"
            "/approve <project> — одобрить чекпоинт\n"
            "/revise <project> <feedback> — переделать с фидбеком\n"
            "/regen <project> — перегенерировать без фидбека\n"
        )

    async def cmd_status(self, update, context):
        projects = self._scan_projects()
        if not projects:
            await update.message.reply_text("Нет активных проектов.")
            return

        lines = ["🧊 Активные проекты:\n"]
        for state in projects:
            stage_name = Stage(state.current_stage).name
            status = state.stages_status.get(state.current_stage.value, "—")
            lines.append(f"• `{state.project_id}` — Stage {state.current_stage.value} ({stage_name}) — {status}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cmd_projects(self, update, context):
        await self.cmd_status(update, context)

    async def cmd_approve(self, update, context):
        if not context.args:
            await update.message.reply_text("Использование: /approve <project_id>")
            return

        project_id = context.args[0]
        flag_file = Path(self.settings.projects_dir) / project_id / ".approve"
        flag_file.touch()
        await update.message.reply_text(f"✅ Одобрено: {project_id}\nПродолжаем со следующего этапа.")

    async def cmd_revise(self, update, context):
        if len(context.args) < 2:
            await update.message.reply_text("Использование: /revise <project_id> <фидбек>")
            return

        project_id = context.args[0]
        feedback = " ".join(context.args[1:])

        # Сохраняем фидбек в файл — пайплайн его подхватит
        feedback_file = Path(self.settings.projects_dir) / project_id / ".revise"
        feedback_file.write_text(feedback, encoding="utf-8")
        await update.message.reply_text(f"📝 Фидбек принят для {project_id}:\n«{feedback}»\nПерезапускаю этап.")

    async def cmd_regen(self, update, context):
        if not context.args:
            await update.message.reply_text("Использование: /regen <project_id>")
            return

        project_id = context.args[0]
        flag_file = Path(self.settings.projects_dir) / project_id / ".regen"
        flag_file.touch()
        await update.message.reply_text(f"🔄 Перегенерация: {project_id}")

    async def callback_handler(self, update, context):
        query = update.callback_query
        await query.answer()
        # Inline-кнопки в уведомлениях

    def _scan_projects(self) -> list:
        projects_dir = Path(self.settings.projects_dir)
        if not projects_dir.exists():
            return []
        states = []
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            try:
                manager = StateManager(project_dir)
                if manager.exists():
                    states.append(manager.load())
            except Exception as e:
                log.warning(f"Не удалось загрузить {project_dir}: {e}")
        return states

    def run(self):
        log.info("[bold cyan]Telegram bot запущен[/]")
        self.app.run_polling()


async def send_notification(message: str, parse_mode: str = "Markdown"):
    """Отправить уведомление в чат (для использования из stages)."""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.warning("Telegram не настроен, пропускаем уведомление")
        return

    from telegram import Bot
    bot = Bot(token=settings.telegram_bot_token)
    try:
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=message,
            parse_mode=parse_mode,
        )
    except Exception as e:
        log.error(f"Ошибка отправки в Telegram: {e}")


def notify(message: str):
    """Синхронная обёртка над send_notification для использования из обычного кода."""
    try:
        asyncio.run(send_notification(message))
    except Exception as e:
        log.error(f"notify failed: {e}")


if __name__ == "__main__":
    bot = WebikTelegramBot()
    bot.run()
