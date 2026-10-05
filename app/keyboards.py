from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.texts import PET_TYPES, PRICE_BANDS, RARITIES


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить"), KeyboardButton(text="💰 Продать")],
            [KeyboardButton(text="👤 Личный кабинет"), KeyboardButton(text="☎️ Поддержка")],
            [KeyboardButton(text="🛡️ Правила / Отзывы")],
        ],
        resize_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ В меню")]],
        resize_keyboard=True,
    )


def buy_menu(webapp_url: str = "") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🐾 Петы Adopt Me", callback_data="buy:pets")],
        [InlineKeyboardButton(text="💎 Робуксы (Robux)", callback_data="buy:robux")],
    ]
    if webapp_url:
        rows.insert(
            0,
            [InlineKeyboardButton(text="🌐 Каталог WebApp", web_app=WebAppInfo(url=webapp_url))],
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sell_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐾 Продать пета", callback_data="sell:pets")],
            [InlineKeyboardButton(text="💎 Продать Robux", callback_data="sell:robux")],
        ]
    )


def reviews_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📜 Правила", callback_data="info:rules")],
            [InlineKeyboardButton(text="⭐ Отзывы", callback_data="info:reviews")],
        ]
    )


def yes_no_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="bargain:yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="bargain:no"),
            ]
        ]
    )


def paid_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid:{order_id}")]]
    )


def robux_calc_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="₽ → R$", callback_data="calc:rub")],
            [InlineKeyboardButton(text="R$ → ₽", callback_data="calc:robux")],
        ]
    )


def catalog_kb(
    products: list,
    rarity: str | None,
    pet_type: str | None,
    price_band: str,
    page: int,
    per_page: int = 5,
) -> InlineKeyboardMarkup:
    start = page * per_page
    chunk = products[start : start + per_page]
    rows: list[list[InlineKeyboardButton]] = []
    for p in chunk:
        stock = "✅" if p["in_stock"] else "⛔"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{stock} {p['name']} · {p['pet_type']} · {p['price_rub']:.0f}РБ",
                    callback_data=f"pet:{p['id']}",
                )
            ]
        )
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"cat:{rarity or '-'}:{pet_type or '-'}:{price_band}:{page-1}"))
    if start + per_page < len(products):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"cat:{rarity or '-'}:{pet_type or '-'}:{price_band}:{page+1}"))
    if nav:
        rows.append(nav)

    rarity_row = [
        InlineKeyboardButton(
            text=("• " if rarity == r else "") + r[:6],
            callback_data=f"cat:{r}:{pet_type or '-'}:{price_band}:0",
        )
        for r in RARITIES
    ]
    rows.append(rarity_row[:3])
    rows.append(rarity_row[3:])
    rows.append(
        [
            InlineKeyboardButton(
                text=("• " if pet_type == t else "") + t,
                callback_data=f"cat:{rarity or '-'}:{t}:{price_band}:0",
            )
            for t in PET_TYPES
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=("• " if price_band == code else "") + label,
                callback_data=f"cat:{rarity or '-'}:{pet_type or '-'}:{code}:0",
            )
            for code, label in PRICE_BANDS
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(text="♻️ Сбросить", callback_data="cat:-:-:any:0"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="back:buy"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_card_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить", callback_data=f"buypet:{product_id}")],
            [InlineKeyboardButton(text="◀️ К каталогу", callback_data="cat:-:-:any:0")],
        ]
    )


def ticket_admin_kb(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"tk:ok:{ticket_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"tk:no:{ticket_id}"),
            ],
            [InlineKeyboardButton(text="💬 Начать диалог", callback_data=f"tk:chat:{ticket_id}")],
        ]
    )


def admin_root_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💱 Курсы Robux", callback_data="adm:rates")],
            [InlineKeyboardButton(text="📦 Каталог петов", callback_data="adm:catalog")],
            [InlineKeyboardButton(text="✏️ Тексты", callback_data="adm:texts")],
            [InlineKeyboardButton(text="📣 Рассылка", callback_data="adm:broadcast")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="adm:stats")],
        ]
    )


def admin_texts_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Приветствие", callback_data="admtext:welcome")],
            [InlineKeyboardButton(text="Правила", callback_data="admtext:rules")],
            [InlineKeyboardButton(text="Отзывы", callback_data="admtext:reviews")],
            [InlineKeyboardButton(text="Реквизиты", callback_data="admtext:payment")],
            [InlineKeyboardButton(text="◀️ Админка", callback_data="adm:root")],
        ]
    )


def admin_catalog_kb(products: list) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if p['in_stock'] else '⛔'} #{p['id']} {p['name']} {p['price_rub']:.0f}₽",
                callback_data=f"admp:{p['id']}",
            )
        ]
        for p in products[:20]
    ]
    rows.append([InlineKeyboardButton(text="➕ Добавить пета", callback_data="adm:addpet")])
    rows.append([InlineKeyboardButton(text="◀️ Админка", callback_data="adm:root")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_product_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💲 Изменить цену", callback_data=f"admedit:{product_id}")],
            [InlineKeyboardButton(text="📦 Наличие вкл/выкл", callback_data=f"admstock:{product_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admdel:{product_id}")],
            [InlineKeyboardButton(text="◀️ Каталог", callback_data="adm:catalog")],
        ]
    )


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Отправить всем", callback_data="bcast:go"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="bcast:no"),
            ]
        ]
    )
