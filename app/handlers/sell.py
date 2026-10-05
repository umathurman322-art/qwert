from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db.repository import Repo
from app.keyboards import cancel_kb, yes_no_kb
from app.services.parse import parse_positive_number
from app.services.tickets import publish_ticket
from app.states import SellPetSG, SellRobuxSG

router = Router()


@router.callback_query(F.data == "sell:pets")
async def sell_pet_start(call: CallbackQuery, state: FSMContext, repo: Repo) -> None:
    await call.answer()
    await state.set_state(SellPetSG.name)
    await call.message.answer(await repo.text("sell_pet_intro"), reply_markup=cancel_kb())


@router.message(SellPetSG.name)
async def sell_pet_name(message: Message, state: FSMContext, repo: Repo) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Название слишком короткое. Напишите ещё раз.")
        return
    await state.update_data(pet_name=name)
    await state.set_state(SellPetSG.qty)
    await message.answer(await repo.text("sell_pet_qty"))


@router.message(SellPetSG.qty)
async def sell_pet_qty(message: Message, state: FSMContext, repo: Repo) -> None:
    qty = parse_positive_number(message.text)
    if qty is None:
        await message.answer(await repo.text("invalid_number"))
        return
    await state.update_data(qty=int(qty))
    await state.set_state(SellPetSG.price)
    await message.answer(await repo.text("sell_pet_price"))


@router.message(SellPetSG.price)
async def sell_pet_price(message: Message, state: FSMContext, repo: Repo) -> None:
    price = parse_positive_number(message.text)
    if price is None:
        await message.answer(await repo.text("invalid_number"))
        return
    await state.update_data(price=price)
    await state.set_state(SellPetSG.bargain)
    await message.answer(await repo.text("sell_pet_bargain"), reply_markup=yes_no_kb())


@router.callback_query(SellPetSG.bargain, F.data.startswith("bargain:"))
async def sell_pet_done(call: CallbackQuery, state: FSMContext, repo: Repo) -> None:
    await call.answer()
    bargain = "да" if call.data.endswith("yes") else "нет"
    data = await state.get_data()
    await state.clear()
    payload = {
        "name": data.get("pet_name"),
        "qty": data.get("qty"),
        "price": data.get("price"),
        "bargain": bargain,
    }
    amount = float(data.get("price") or 0)
    order_id = await repo.create_order(call.from_user.id, "sell_pet", payload, amount)
    body = (
        f"💰 <b>Скупка пета</b>\n"
        f"Пет: {payload['name']}\n"
        f"Кол-во: {payload['qty']}\n"
        f"Желаемая цена: {amount:.0f} ₽\n"
        f"Торг: {bargain}"
    )
    chat_id = settings.admin_chat_id or settings.support_chat_id
    if not chat_id:
        await call.message.answer("Чат админов не настроен (ADMIN_CHAT_ID).")
        return
    ticket_id = await publish_ticket(
        call.bot, repo, chat_id, call.from_user.id, call.from_user.username, "sell_pet", body, order_id
    )
    await repo.add_deal_log(call.from_user.id, f"Анкета продажи {payload['name']}", amount)
    text = (await repo.text("ticket_created")).format(ticket_id=ticket_id)
    await call.message.answer(text)


@router.callback_query(F.data == "sell:robux")
async def sell_robux_start(call: CallbackQuery, state: FSMContext, repo: Repo) -> None:
    await call.answer()
    _sell, buy = await repo.robux_rates()
    await state.set_state(SellRobuxSG.amount)
    await call.message.answer(
        f"💎 Скупка Robux. Курс: <b>{buy:g} R$ = 1 ₽</b> выплаты.\n"
        + await repo.text("sell_robux_amount"),
        reply_markup=cancel_kb(),
    )


@router.message(SellRobuxSG.amount)
async def sell_robux_amount(message: Message, state: FSMContext, repo: Repo) -> None:
    amount = parse_positive_number(message.text)
    if amount is None:
        await message.answer(await repo.text("invalid_number"))
        return
    await state.update_data(robux=amount)
    await state.set_state(SellRobuxSG.method)
    await message.answer(await repo.text("sell_robux_method"))


@router.message(SellRobuxSG.method)
async def sell_robux_done(message: Message, state: FSMContext, repo: Repo) -> None:
    method = (message.text or "").strip()
    if len(method) < 2:
        await message.answer("Опишите способ передачи чуть подробнее.")
        return
    data = await state.get_data()
    await state.clear()
    rbx = float(data.get("robux") or 0)
    _sell, buy_rate = await repo.robux_rates()
    payout = rbx / buy_rate if buy_rate else 0
    payload = {"robux": rbx, "method": method, "payout": payout, "rate": buy_rate}
    order_id = await repo.create_order(message.from_user.id, "sell_robux", payload, payout)
    body = (
        f"💰 <b>Скупка Robux</b>\n"
        f"Количество: {rbx:.0f} R$\n"
        f"Способ: {method}\n"
        f"Выплата ≈ <b>{payout:.2f} ₽</b>\n"
        f"Курс скупки: {buy_rate:g} R$ / ₽"
    )
    chat_id = settings.admin_chat_id or settings.support_chat_id
    if not chat_id:
        await message.answer("Чат админов не настроен.")
        return
    ticket_id = await publish_ticket(
        message.bot, repo, chat_id, message.from_user.id, message.from_user.username, "sell_robux", body, order_id
    )
    await repo.add_deal_log(message.from_user.id, f"Скупка {rbx:.0f} R$", payout)
    await message.answer((await repo.text("ticket_created")).format(ticket_id=ticket_id) + f"\nОриентир выплаты: {payout:.2f} ₽")
