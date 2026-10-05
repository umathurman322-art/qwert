from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import settings
from app.db.repository import Repo
from app.keyboards import cancel_kb
from app.services.tickets import publish_ticket
from app.states import SupportSG

router = Router()


@router.message(F.text == "☎️ Поддержка")
async def support_start(message: Message, state: FSMContext, repo: Repo) -> None:
    await state.set_state(SupportSG.waiting)
    await message.answer(await repo.text("support_prompt"), reply_markup=cancel_kb())


@router.message(SupportSG.waiting, F.content_type.in_({"text", "photo"}))
async def support_message(message: Message, state: FSMContext, repo: Repo) -> None:
    chat_id = settings.support_chat_id or settings.admin_chat_id
    if not chat_id:
        await message.answer("Чат поддержки не настроен (SUPPORT_CHAT_ID).")
        return
    body = message.caption or message.text or "Фото без подписи"
    if message.photo:
        body = "📷 Фото\n" + body
    ticket_id = await publish_ticket(
        message.bot,
        repo,
        chat_id,
        message.from_user.id,
        message.from_user.username,
        "support",
        body,
    )
    if message.photo:
        copied = await message.bot.send_photo(
            chat_id, message.photo[-1].file_id, caption=f"Вложение к тикету #{ticket_id}"
        )
        await repo.bind_message(chat_id, copied.message_id, ticket_id)
    await repo.set_ticket_status(ticket_id, "dialog")
    await state.clear()
    await message.answer(await repo.text("support_sent"))
