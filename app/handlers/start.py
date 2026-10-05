from __future__ import annotations

import random

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import settings
from app.db.repository import Repo
from app.keyboards import main_menu
from app.services.captcha import image_captcha, math_captcha
from app.states import CaptchaSG

router = Router()


async def send_captcha(message: Message, state: FSMContext, repo: Repo) -> None:
    prompt = await repo.text("captcha_text")
    img_prompt = await repo.text("captcha_image")
    if random.random() < 0.5:
        question, answer = math_captcha()
        await state.update_data(captcha=answer)
        await message.answer(prompt.format(question=question))
    else:
        file, answer = image_captcha()
        await state.update_data(captcha=answer)
        await message.answer_photo(file, caption=img_prompt)
    await state.set_state(CaptchaSG.waiting)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, repo: Repo) -> None:
    await state.clear()
    user = message.from_user
    referred_by = None
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2 and parts[1].startswith("ref_"):
        try:
            ref_id = int(parts[1][4:])
            if ref_id != user.id:
                referred_by = ref_id
        except ValueError:
            referred_by = None
    role = "admin" if settings.is_admin(user.id) else "user"
    await repo.upsert_user(user.id, user.username, user.full_name, referred_by, role)
    db_user = await repo.get_user(user.id)
    if settings.is_admin(user.id) or (db_user and int(db_user["captcha_passed"]) == 1):
        if settings.is_admin(user.id):
            await repo.set_captcha_passed(user.id)
        text = await repo.text("welcome")
        await message.answer(text, reply_markup=main_menu())
        return
    await send_captcha(message, state, repo)


@router.message(CaptchaSG.waiting)
async def captcha_answer(message: Message, state: FSMContext, repo: Repo) -> None:
    data = await state.get_data()
    expected = str(data.get("captcha", ""))
    if not message.text or message.text.strip() != expected:
        fail = await repo.text("captcha_fail")
        await message.answer(fail)
        await send_captcha(message, state, repo)
        return
    await repo.set_captcha_passed(message.from_user.id)
    await state.clear()
    ok = await repo.text("captcha_ok")
    welcome = await repo.text("welcome")
    await message.answer(ok)
    await message.answer(welcome, reply_markup=main_menu())
