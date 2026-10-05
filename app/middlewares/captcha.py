from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import settings
from app.db.repository import Repo
from app.states import CaptchaSG

ALLOWED_PREFIXES = ("/start",)


class CaptchaMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        repo: Repo = data["repo"]
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)
        if settings.is_admin(user.id):
            return await handler(event, data)

        db_user = await repo.get_user(user.id)
        if db_user and int(db_user["captcha_passed"]) == 1:
            return await handler(event, data)

        state: FSMContext | None = data.get("state")
        current = await state.get_state() if state else None
        if current == CaptchaSG.waiting.state:
            return await handler(event, data)

        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)
        if isinstance(event, Message) and event.text and event.text.strip() in ALLOWED_PREFIXES:
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("Сначала пройдите капчу: /start", show_alert=True)
            return None
        if isinstance(event, Message):
            await event.answer("🛡️ Сначала пройдите проверку. Нажмите /start")
            return None
        return None
