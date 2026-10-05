from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.repository import Repo
from app.keyboards import buy_menu, main_menu, reviews_menu, sell_menu
from app.config import settings

router = Router()


@router.message(F.text == "◀️ В меню")
async def back_menu(message: Message, state: FSMContext, repo: Repo) -> None:
    await state.clear()
    await message.answer(await repo.text("cancelled"), reply_markup=main_menu())


@router.message(F.text == "🛒 Купить")
async def buy_entry(message: Message, repo: Repo) -> None:
    await message.answer("Что хотите купить?", reply_markup=buy_menu(settings.webapp_url))


@router.callback_query(F.data == "back:buy")
async def buy_back(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.edit_text("Что хотите купить?", reply_markup=buy_menu(settings.webapp_url))


@router.message(F.text == "💰 Продать")
async def sell_entry(message: Message) -> None:
    await message.answer("Что хотите продать?", reply_markup=sell_menu())


@router.message(F.text == "🛡️ Правила / Отзывы")
async def info_entry(message: Message) -> None:
    await message.answer("Выберите раздел:", reply_markup=reviews_menu())


@router.callback_query(F.data == "info:rules")
async def info_rules(call: CallbackQuery, repo: Repo) -> None:
    await call.answer()
    await call.message.answer(await repo.text("rules"))


@router.callback_query(F.data == "info:reviews")
async def info_reviews(call: CallbackQuery, repo: Repo) -> None:
    await call.answer()
    await call.message.answer(await repo.text("reviews"))
