from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class CaptchaSG(StatesGroup):
    waiting = State()


class BuyRobuxSG(StatesGroup):
    amount = State()


class SellPetSG(StatesGroup):
    name = State()
    qty = State()
    price = State()
    bargain = State()


class SellRobuxSG(StatesGroup):
    amount = State()
    method = State()


class SupportSG(StatesGroup):
    waiting = State()


class AdminRateSG(StatesGroup):
    sell = State()
    buy = State()


class AdminProductSG(StatesGroup):
    name = State()
    rarity = State()
    pet_type = State()
    price = State()


class AdminEditPriceSG(StatesGroup):
    product_id = State()
    price = State()


class AdminTextSG(StatesGroup):
    key = State()
    value = State()


class AdminBroadcastSG(StatesGroup):
    content = State()
    confirm = State()
