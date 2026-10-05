from __future__ import annotations

from app.db.repository import Database

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    captcha_passed INTEGER NOT NULL DEFAULT 0,
    balance_rub REAL NOT NULL DEFAULT 0,
    referred_by INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rarity TEXT NOT NULL,
    pet_type TEXT NOT NULL,
    price_rub REAL NOT NULL,
    in_stock INTEGER NOT NULL DEFAULT 1,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_tg_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    payload TEXT NOT NULL DEFAULT '{}',
    amount_rub REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_tg_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    order_id INTEGER,
    work_chat_id INTEGER,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ticket_links (
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    ticket_id INTEGER NOT NULL,
    PRIMARY KEY (chat_id, message_id)
);

CREATE TABLE IF NOT EXISTS deal_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_tg_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    amount_rub REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SEED_PRODUCTS = [
    ("Shadow Dragon", "Legendary", "Normal", 4500, 1, "Классика Adopt Me"),
    ("Shadow Dragon", "Legendary", "Neon", 8900, 1, "Neon Shadow"),
    ("Frost Dragon", "Legendary", "Mega-Neon", 15000, 1, "Mega Neon Frost"),
    ("Bat Dragon", "Legendary", "Normal", 5200, 0, "Нет в наличии"),
    ("Owl", "Legendary", "Neon", 6100, 1, ""),
    ("Dalmatian", "Ultra-Rare", "Mega-Neon", 1800, 1, ""),
    ("Turtle", "Legendary", "Normal", 2100, 1, ""),
    ("Flamingo", "Ultra-Rare", "Neon", 950, 1, ""),
    ("Cat", "Common", "Normal", 80, 1, ""),
    ("Dog", "Common", "Neon", 150, 1, ""),
]

SEED_SETTINGS = {
    "robux_sell_rate": "3",  # R$ за 1 ₽ при покупке пользователем
    "robux_buy_rate": "4",  # R$ за 1 ₽ при скупке у пользователя
    "text_welcome": "",
    "text_rules": "",
    "text_reviews": "",
    "text_payment": "",
}


async def init_db(db: Database) -> None:
    await db.executescript(SCHEMA)
    for key, value in SEED_SETTINGS.items():
        await db.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
            (key, value),
        )
    count = await db.fetchval("SELECT COUNT(*) FROM products")
    if not count:
        for row in SEED_PRODUCTS:
            await db.execute(
                """
                INSERT INTO products(name, rarity, pet_type, price_rub, in_stock, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                row,
            )
    await db.commit()
