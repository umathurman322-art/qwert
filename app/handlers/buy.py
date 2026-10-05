from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db.repository import Repo
from app.keyboards import catalog_kb, paid_kb, product_card_kb, robux_calc_kb
from app.services.parse import parse_catalog_callback, parse_positive_number, parse_price_band
from app.services.tickets import publish_ticket
from app.states import BuyRobuxSG
from app.texts import DEFAULT_TEXTS

router = Router()


async def show_catalog(target: Message, repo: Repo, data: str) -> None:
    rarity, pet_type, band, page = parse_catalog_callback(data)
    lo, hi = parse_price_band(band)
    items = await repo.list_products(rarity=rarity, pet_type=pet_type, price_from=lo, price_to=hi)
    header = (
        f"🐾 <b>Каталог петов</b>\n"
        f"Фильтр: {rarity or 'все редкости'} · {pet_type or 'все типы'} · {band}\n"
        f"Найдено: {len(items)}"
    )
    if not items:
        header = DEFAULT_TEXTS["empty_catalog"]
    markup = catalog_kb(items, rarity, pet_type, band, page)
    try:
        await target.edit_text(header, reply_markup=markup)
    except Exception:
        await target.answer(header, reply_markup=markup)


@router.callback_query(F.data == "buy:pets")
async def buy_pets(call: CallbackQuery, repo: Repo) -> None:
    await call.answer()
    rarity, pet_type, band, page = None, None, "any", 0
    items = await repo.list_products()
    await call.message.edit_text(
        f"🐾 <b>Каталог петов</b>\nНайдено: {len(items)}",
        reply_markup=catalog_kb(items, rarity, pet_type, band, page),
    )


@router.callback_query(F.data.startswith("cat:"))
async def catalog_nav(call: CallbackQuery, repo: Repo) -> None:
    await call.answer()
    await show_catalog(call.message, repo, call.data)


@router.callback_query(F.data.startswith("pet:"))
async def pet_card(call: CallbackQuery, repo: Repo) -> None:
    await call.answer()
    product_id = int(call.data.split(":")[1])
    p = await repo.get_product(product_id)
    if not p:
        await call.message.answer("Товар не найден.")
        return
    stock = "в наличии" if p["in_stock"] else "нет на складе"
    text = (
        f"🐾 <b>{p['name']}</b>\n"
        f"Редкость: {p['rarity']}\n"
        f"Тип: {p['pet_type']}\n"
        f"Цена: <b>{p['price_rub']:.0f} РБ</b>\n"
        f"Статус: {stock}\n"
        f"{p['description'] or ''}"
    )
    await call.message.answer(text, reply_markup=product_card_kb(product_id))


@router.callback_query(F.data.startswith("buypet:"))
async def buy_pet(call: CallbackQuery, repo: Repo) -> None:
    product_id = int(call.data.split(":")[1])
    p = await repo.get_product(product_id)
    if not p or not p["in_stock"]:
        await call.answer(DEFAULT_TEXTS["out_of_stock"], show_alert=True)
        return
    await call.answer()
    payload = {"product_id": product_id, "name": p["name"], "type": p["pet_type"]}
    order_id = await repo.create_order(call.from_user.id, "buy_pet", payload, float(p["price_rub"]))
    details = await repo.get_setting("text_payment", settings.payment_details)
    text = (await repo.text("payment_wait")).format(order_id=order_id, details=details)
    await call.message.answer(text, reply_markup=paid_kb(order_id))
    if settings.admin_chat_id:
        body = (
            f"🛒 Покупка пета\n"
            f"{p['name']} ({p['pet_type']})\n"
            f"Сумма: {p['price_rub']:.0f} РБ\nОжидает оплату."
        )
        await publish_ticket(
            call.bot, repo, settings.admin_chat_id, call.from_user.id, call.from_user.username, "buy", body, order_id
        )


@router.callback_query(F.data == "buy:robux")
async def buy_robux(call: CallbackQuery, repo: Repo) -> None:
    await call.answer()
    sell, _buy = await repo.robux_rates()
    await call.message.edit_text(
        f"💎 <b>Покупка Robux</b>\n"
        f"Курс продажи: <b>1 ₽ = {sell:g} R$</b>\n\n"
        f"Выберите направление калькулятора:",
        reply_markup=robux_calc_kb(),
    )


@router.callback_query(F.data.in_({"calc:rub", "calc:robux"}))
async def calc_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    mode = "rub" if call.data.endswith("rub") else "robux"
    await state.set_state(BuyRobuxSG.amount)
    await state.update_data(calc_mode=mode)
    hint = "сумму в рублях" if mode == "rub" else "количество Robux"
    await call.message.answer(f"Введите {hint} (только число).")


@router.message(BuyRobuxSG.amount)
async def calc_amount(message: Message, state: FSMContext, repo: Repo) -> None:
    value = parse_positive_number(message.text)
    if value is None:
        await message.answer(await repo.text("invalid_number"))
        return
    data = await state.get_data()
    sell, _buy = await repo.robux_rates()
    mode = data.get("calc_mode", "rub")
    if mode == "rub":
        rub, rbx = value, value * sell
    else:
        rbx, rub = value, value / sell if sell else 0
    payload = {"rub": rub, "robux": rbx, "rate": sell}
    order_id = await repo.create_order(message.from_user.id, "buy_robux", payload, rub)
    await state.clear()
    details = await repo.get_setting("text_payment", settings.payment_details)
    await message.answer(
        f"💎 К оплате: <b>{rub:.2f} ₽</b>\nВы получите ≈ <b>{rbx:.0f} R$</b>\n\n"
        + (await repo.text("payment_wait")).format(order_id=order_id, details=details),
        reply_markup=paid_kb(order_id),
    )
    if settings.admin_chat_id:
        body = f"🛒 Покупка Robux\n{rbx:.0f} R$ за {rub:.2f} ₽\nКурс {sell:g}"
        await publish_ticket(
            message.bot,
            repo,
            settings.admin_chat_id,
            message.from_user.id,
            message.from_user.username,
            "buy",
            body,
            order_id,
        )


@router.callback_query(F.data.startswith("paid:"))
async def user_paid(call: CallbackQuery, repo: Repo) -> None:
    order_id = int(call.data.split(":")[1])
    order = await repo.get_order(order_id)
    if not order or int(order["user_tg_id"]) != call.from_user.id:
        await call.answer("Заявка не найдена", show_alert=True)
        return
    await repo.set_order_status(order_id, "awaiting_payment")
    await call.answer()
    await call.message.answer("⏳ Отметили «оплачено». Админ проверит и откроет передачу товара.")
    if settings.admin_chat_id:
        await call.bot.send_message(
            settings.admin_chat_id,
            f"💸 Пользователь <code>{call.from_user.id}</code> отметил оплату по заявке #{order_id}.\n"
            f"Примите тикет кнопкой ✅ или напишите Reply.",
        )


@router.message(F.web_app_data)
async def from_webapp(message: Message, repo: Repo) -> None:
    try:
        payload = json.loads(message.web_app_data.data)
        product_id = int(payload["product_id"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        await message.answer("Некорректные данные каталога.")
        return
    p = await repo.get_product(product_id)
    if not p:
        await message.answer("Товар не найден.")
        return
    stock = "в наличии" if p["in_stock"] else "нет на складе"
    await message.answer(
        f"🐾 <b>{p['name']}</b>\n{p['rarity']} · {p['pet_type']}\n"
        f"{p['price_rub']:.0f} РБ · {stock}",
        reply_markup=product_card_kb(product_id),
    )
