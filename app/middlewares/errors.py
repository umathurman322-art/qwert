from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Update failed: %s", event)
            bot = data.get("bot")
            update = event if isinstance(event, Update) else data.get("event_update")
            chat_id = None
            if isinstance(update, Update):
                if update.message:
                    chat_id = update.message.chat.id
                elif update.callback_query and update.callback_query.message:
                    chat_id = update.callback_query.message.chat.id
            if bot and chat_id:
                try:
                    await bot.send_message(chat_id, "⚠️ Произошла ошибка. Попробуйте ещё раз или /start.")
                except Exception:
                    pass
            return None
