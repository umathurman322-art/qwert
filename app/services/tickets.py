from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

from app.db.repository import Repo
from app.keyboards import ticket_admin_kb


async def publish_ticket(
    bot: Bot,
    repo: Repo,
    chat_id: int,
    user_tg_id: int,
    username: str | None,
    kind: str,
    body: str,
    order_id: int | None = None,
) -> int:
    ticket_id = await repo.create_ticket(user_tg_id, kind, chat_id, order_id)
    uname = f"@{username}" if username else "без username"
    text = (
        f"🎫 <b>Тикет #{ticket_id}</b> · {kind}\n"
        f"👤 {uname} · <code>{user_tg_id}</code>\n"
    )
    if order_id:
        text += f"🧾 Заявка #{order_id}\n"
    text += f"\n{body}\n\n↩️ Ответьте Reply на это сообщение — пользователь получит ответ в боте."
    msg = await bot.send_message(chat_id, text, reply_markup=ticket_admin_kb(ticket_id))
    await repo.bind_message(chat_id, msg.message_id, ticket_id)
    return ticket_id


async def relay_to_user(bot: Bot, repo: Repo, ticket, src: Message) -> None:
    user_id = int(ticket["user_tg_id"])
    if src.photo:
        file_id = src.photo[-1].file_id
        sent = await bot.send_photo(
            user_id, file_id, caption=src.caption or "📷 Сообщение поддержки", parse_mode=None
        )
    elif src.text:
        sent = await bot.send_message(user_id, f"💬 Поддержка:\n{src.text}", parse_mode=None)
    else:
        sent = await bot.send_message(
            user_id, "💬 Поддержка отправила вложение. Напишите, если нужно уточнение.", parse_mode=None
        )
    await repo.bind_message(sent.chat.id, sent.message_id, int(ticket["id"]))


async def relay_to_staff(bot: Bot, repo: Repo, ticket, src: Message) -> None:
    chat_id = int(ticket["work_chat_id"])
    prefix = f"👤 Пользователь <code>{src.from_user.id}</code> · тикет #{ticket['id']}"
    # Reply to latest known staff message if possible — we reply without specific id if unknown
    if src.photo:
        file_id = src.photo[-1].file_id
        sent = await bot.send_photo(
            chat_id, file_id, caption=f"{prefix}\n{src.caption or ''}", parse_mode=None
        )
    elif src.text:
        sent = await bot.send_message(chat_id, f"{prefix}\n{src.text}", parse_mode=None)
    else:
        sent = await bot.send_message(chat_id, f"{prefix}\n(нетекст)", parse_mode=None)
    await repo.bind_message(chat_id, sent.message_id, int(ticket["id"]))
