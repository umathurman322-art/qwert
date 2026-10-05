from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db.repository import Repo
from app.keyboards import (
    admin_catalog_kb,
    admin_product_kb,
    admin_root_kb,
    admin_texts_kb,
    confirm_broadcast_kb,
)
from app.services.parse import parse_positive_number
from app.states import AdminBroadcastSG, AdminEditPriceSG, AdminProductSG, AdminRateSG, AdminTextSG
from app.texts import PET_TYPES, RARITIES

router = Router()
logger = logging.getLogger(__name__)


def admin_only(user_id: int) -> bool:
    return settings.is_admin(user_id)


@router.message(Command("admin"))
async def admin_entry(message: Message) -> None:
    if not admin_only(message.from_user.id):
        await message.answer("⛔ Недостаточно прав.")
        return
    await message.answer("⚙️ <b>Админ-панель</b>", reply_markup=admin_root_kb())


@router.callback_query(F.data == "adm:root")
async def admin_root(call: CallbackQuery) -> None:
    if not admin_only(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    await call.answer()
    await call.message.edit_text("⚙️ <b>Админ-панель</b>", reply_markup=admin_root_kb())


@router.callback_query(F.data == "adm:rates")
async def admin_rates(call: CallbackQuery, state: FSMContext, repo: Repo) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    sell, buy = await repo.robux_rates()
    await state.set_state(AdminRateSG.sell)
    await call.message.answer(
        f"Текущий курс продажи (R$ за 1 ₽): <b>{sell:g}</b>\n"
        f"Текущий курс скупки (R$ за 1 ₽ выплаты): <b>{buy:g}</b>\n\n"
        f"Отправьте новый курс <b>продажи</b> числом."
    )


@router.message(AdminRateSG.sell)
async def admin_rate_sell(message: Message, state: FSMContext, repo: Repo) -> None:
    if not admin_only(message.from_user.id):
        return
    value = parse_positive_number(message.text)
    if value is None:
        await message.answer("Нужно положительное число.")
        return
    await state.update_data(sell=value)
    await state.set_state(AdminRateSG.buy)
    await message.answer("Теперь курс <b>скупки</b> (сколько R$ за 1 ₽ выплаты).")


@router.message(AdminRateSG.buy)
async def admin_rate_buy(message: Message, state: FSMContext, repo: Repo) -> None:
    if not admin_only(message.from_user.id):
        return
    value = parse_positive_number(message.text)
    if value is None:
        await message.answer("Нужно положительное число.")
        return
    data = await state.get_data()
    await state.clear()
    await repo.set_setting("robux_sell_rate", str(data["sell"]))
    await repo.set_setting("robux_buy_rate", str(value))
    await message.answer(
        f"✅ Курсы обновлены.\nПродажа: {data['sell']:g} R$/₽\nСкупка: {value:g} R$/₽",
        reply_markup=admin_root_kb(),
    )


@router.callback_query(F.data == "adm:catalog")
async def admin_catalog(call: CallbackQuery, repo: Repo) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    products = await repo.list_products()
    await call.message.edit_text("📦 Каталог (макс. 20 в списке):", reply_markup=admin_catalog_kb(products))


@router.callback_query(F.data.startswith("admp:"))
async def admin_product(call: CallbackQuery, repo: Repo) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    pid = int(call.data.split(":")[1])
    p = await repo.get_product(pid)
    if not p:
        await call.message.answer("Товар не найден")
        return
    await call.message.answer(
        f"#{p['id']} {p['name']}\n{p['rarity']} · {p['pet_type']}\n"
        f"{p['price_rub']:.0f} ₽ · stock={p['in_stock']}",
        reply_markup=admin_product_kb(pid),
    )


@router.callback_query(F.data.startswith("admstock:"))
async def admin_stock(call: CallbackQuery, repo: Repo) -> None:
    if not admin_only(call.from_user.id):
        return
    pid = int(call.data.split(":")[1])
    flag = await repo.toggle_stock(pid)
    await call.answer("В наличии" if flag else "Нет на складе", show_alert=True)


@router.callback_query(F.data.startswith("admdel:"))
async def admin_del(call: CallbackQuery, repo: Repo) -> None:
    if not admin_only(call.from_user.id):
        return
    pid = int(call.data.split(":")[1])
    await repo.delete_product(pid)
    await call.answer("Удалено")
    products = await repo.list_products()
    await call.message.answer("Каталог обновлён", reply_markup=admin_catalog_kb(products))


@router.callback_query(F.data.startswith("admedit:"))
async def admin_edit_price(call: CallbackQuery, state: FSMContext) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    pid = int(call.data.split(":")[1])
    await state.set_state(AdminEditPriceSG.price)
    await state.update_data(product_id=pid)
    await call.message.answer("Новая цена в ₽ (число):")


@router.message(AdminEditPriceSG.price)
async def admin_save_price(message: Message, state: FSMContext, repo: Repo) -> None:
    if not admin_only(message.from_user.id):
        return
    price = parse_positive_number(message.text)
    if price is None:
        await message.answer("Нужно число.")
        return
    data = await state.get_data()
    await state.clear()
    await repo.update_product_price(int(data["product_id"]), price)
    await message.answer("✅ Цена обновлена", reply_markup=admin_root_kb())


@router.callback_query(F.data == "adm:addpet")
async def admin_add_pet(call: CallbackQuery, state: FSMContext) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    await state.set_state(AdminProductSG.name)
    await call.message.answer("Название пета:")


@router.message(AdminProductSG.name)
async def add_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=(message.text or "").strip())
    await state.set_state(AdminProductSG.rarity)
    await message.answer("Редкость: " + ", ".join(RARITIES))


@router.message(AdminProductSG.rarity)
async def add_rarity(message: Message, state: FSMContext) -> None:
    rarity = (message.text or "").strip()
    if rarity not in RARITIES:
        await message.answer("Выберите одну из: " + ", ".join(RARITIES))
        return
    await state.update_data(rarity=rarity)
    await state.set_state(AdminProductSG.pet_type)
    await message.answer("Тип: " + ", ".join(PET_TYPES))


@router.message(AdminProductSG.pet_type)
async def add_type(message: Message, state: FSMContext) -> None:
    pet_type = (message.text or "").strip()
    if pet_type not in PET_TYPES:
        await message.answer("Выберите одну из: " + ", ".join(PET_TYPES))
        return
    await state.update_data(pet_type=pet_type)
    await state.set_state(AdminProductSG.price)
    await message.answer("Цена в ₽:")


@router.message(AdminProductSG.price)
async def add_price(message: Message, state: FSMContext, repo: Repo) -> None:
    price = parse_positive_number(message.text)
    if price is None:
        await message.answer("Нужно число.")
        return
    data = await state.get_data()
    await state.clear()
    pid = await repo.add_product(data["name"], data["rarity"], data["pet_type"], price)
    await message.answer(f"✅ Добавлен товар #{pid} {data['name']}", reply_markup=admin_root_kb())


@router.callback_query(F.data == "adm:texts")
async def admin_texts(call: CallbackQuery) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    await call.message.edit_text("Что изменить?", reply_markup=admin_texts_kb())


@router.callback_query(F.data.startswith("admtext:"))
async def admin_text_pick(call: CallbackQuery, state: FSMContext) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    key = call.data.split(":")[1]
    await state.set_state(AdminTextSG.value)
    await state.update_data(key=key)
    await call.message.answer(f"Пришлите новый текст для <b>{key}</b> (HTML можно).")


@router.message(AdminTextSG.value)
async def admin_text_save(message: Message, state: FSMContext, repo: Repo) -> None:
    if not admin_only(message.from_user.id):
        return
    data = await state.get_data()
    await state.clear()
    key = data["key"]
    mapping = {"welcome": "text_welcome", "rules": "text_rules", "reviews": "text_reviews", "payment": "text_payment"}
    await repo.set_setting(mapping[key], message.html_text or message.text or "")
    await message.answer("✅ Текст сохранён", reply_markup=admin_root_kb())


@router.callback_query(F.data == "adm:broadcast")
async def bcast_start(call: CallbackQuery, state: FSMContext) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    await state.set_state(AdminBroadcastSG.content)
    await call.message.answer("Пришлите текст или фото с подписью для рассылки.")


@router.message(AdminBroadcastSG.content)
async def bcast_preview(message: Message, state: FSMContext) -> None:
    if not admin_only(message.from_user.id):
        return
    await state.update_data(
        text=message.html_text or message.text,
        photo=message.photo[-1].file_id if message.photo else None,
        caption=message.caption,
    )
    await state.set_state(AdminBroadcastSG.confirm)
    await message.answer("Отправить это всем пользователям?", reply_markup=confirm_broadcast_kb())


@router.callback_query(AdminBroadcastSG.confirm, F.data == "bcast:no")
async def bcast_no(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer("Отменено")
    await call.message.answer("Рассылка отменена", reply_markup=admin_root_kb())


@router.callback_query(AdminBroadcastSG.confirm, F.data == "bcast:go")
async def bcast_go(call: CallbackQuery, state: FSMContext, repo: Repo) -> None:
    if not admin_only(call.from_user.id):
        return
    data = await state.get_data()
    await state.clear()
    await call.answer("Запускаю")
    ids = await repo.all_user_ids()
    ok = fail = 0
    for uid in ids:
        try:
            if data.get("photo"):
                await call.bot.send_photo(uid, data["photo"], caption=data.get("caption"))
            else:
                await call.bot.send_message(uid, data.get("text") or "")
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await call.message.answer(f"📣 Готово. Успешно: {ok}, ошибок: {fail}", reply_markup=admin_root_kb())


@router.callback_query(F.data == "adm:stats")
async def admin_stats(call: CallbackQuery, repo: Repo) -> None:
    if not admin_only(call.from_user.id):
        return
    await call.answer()
    s = await repo.stats()
    await call.message.answer(
        "📊 <b>Статистика</b>\n"
        f"Пользователи: <b>{s['users']}</b>\n"
        f"Активные сделки: <b>{s['active']}</b>\n"
        f"Открытые тикеты: <b>{s['tickets_open']}</b>\n"
        f"Оборот (принятые/оплаченные): <b>{s['turnover']:.2f} ₽</b>",
        reply_markup=admin_root_kb(),
    )
