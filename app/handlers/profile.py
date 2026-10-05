from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.db.repository import Repo
from app.keyboards import main_menu

router = Router()


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(
        f"Ваш ID: <code>{message.from_user.id}</code>\nЧат: <code>{message.chat.id}</code>"
    )


@router.message(F.text == "👤 Личный кабинет")
async def profile(message: Message, repo: Repo) -> None:
    user = await repo.get_user(message.from_user.id)
    me = await message.bot.get_me()
    ref = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
    text = (await repo.text("profile")).format(
        tg_id=message.from_user.id,
        balance=float(user["balance_rub"]) if user else 0,
        ref_link=ref,
    )
    logs = await repo.deal_history(message.from_user.id)
    if logs:
        text += "\n\n📜 <b>История</b>:\n"
        for row in logs:
            text += f"• {row['title']} — {row['amount_rub']:.0f} ₽\n"
    else:
        text += "\n\nИстория сделок пока пуста."
    await message.answer(text, reply_markup=main_menu())
