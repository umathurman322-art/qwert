from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db.repository import Repo
from app.services.tickets import relay_to_staff, relay_to_user

router = Router()

MENU_TEXTS = {
    "🛒 Купить",
    "💰 Продать",
    "👤 Личный кабинет",
    "☎️ Поддержка",
    "🛡️ Правила / Отзывы",
    "◀️ В меню",
}


def _is_work_chat(chat_id: int) -> bool:
    return chat_id in {settings.admin_chat_id, settings.support_chat_id} and chat_id != 0


@router.callback_query(F.data.startswith("tk:"))
async def ticket_actions(call: CallbackQuery, repo: Repo) -> None:
    _, action, raw_id = call.data.split(":")
    ticket_id = int(raw_id)
    ticket = await repo.get_ticket(ticket_id)
    if not ticket:
        await call.answer("Тикет не найден", show_alert=True)
        return
    user_id = int(ticket["user_tg_id"])
    order_id = ticket["order_id"]
    if action == "ok":
        await repo.set_ticket_status(ticket_id, "dialog")
        if order_id:
            await repo.set_order_status(int(order_id), "accepted")
        await call.bot.send_message(
            user_id,
            f"✅ Ваша заявка #{ticket_id} принята. Напишите сюда — сообщение уйдёт менеджеру.",
        )
        await call.answer("Принято")
        await call.message.answer(f"Тикет #{ticket_id}: принят. Можно писать Reply.")
    elif action == "no":
        await repo.set_ticket_status(ticket_id, "closed")
        if order_id:
            await repo.set_order_status(int(order_id), "rejected")
        await call.bot.send_message(user_id, f"❌ Заявка #{ticket_id} отклонена.")
        await call.answer("Отклонено")
        await call.message.answer(f"Тикет #{ticket_id}: отклонён.")
    else:
        await repo.set_ticket_status(ticket_id, "dialog")
        await call.bot.send_message(
            user_id,
            "💬 Менеджер открыл диалог. Пишите сообщения сюда — они придут в рабочий чат.",
        )
        await call.answer("Диалог открыт")
        await call.message.answer(
            f"Тикет #{ticket_id}: диалог. Отвечайте через Reply на карточку или сообщения ветки."
        )


@router.message(F.reply_to_message, F.chat.type.in_({"group", "supergroup"}))
async def staff_reply(message: Message, repo: Repo) -> None:
    if not _is_work_chat(message.chat.id):
        return
    if message.from_user and message.from_user.is_bot:
        return
    ref = message.reply_to_message
    ticket = await repo.ticket_by_message(message.chat.id, ref.message_id)
    if not ticket:
        return
    if ticket["status"] == "closed":
        await message.reply("Тикет закрыт.")
        return
    await repo.set_ticket_status(int(ticket["id"]), "dialog")
    await relay_to_user(message.bot, repo, ticket, message)
    await repo.bind_message(message.chat.id, message.message_id, int(ticket["id"]))


@router.message(F.chat.type == "private")
async def user_dialog_bridge(message: Message, repo: Repo) -> None:
    if message.text in MENU_TEXTS:
        return
    if message.text and message.text.startswith("/"):
        return
    ticket = await repo.active_dialog(message.from_user.id)
    if not ticket:
        return
    await relay_to_staff(message.bot, repo, ticket, message)
