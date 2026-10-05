from __future__ import annotations

import json
from typing import Any

from app.db.database import Database
from app.texts import DEFAULT_TEXTS


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


class Repo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def upsert_user(
        self,
        tg_id: int,
        username: str | None,
        full_name: str,
        referred_by: int | None,
        role: str,
    ) -> None:
        existing = await self.get_user(tg_id)
        if existing:
            await self.db.execute(
                "UPDATE users SET username=?, full_name=? WHERE tg_id=?",
                (username, full_name, tg_id),
            )
        else:
            await self.db.execute(
                """
                INSERT INTO users(tg_id, username, full_name, referred_by, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tg_id, username, full_name, referred_by, role),
            )
        await self.db.commit()

    async def get_user(self, tg_id: int):
        return await self.db.fetchone("SELECT * FROM users WHERE tg_id=?", (tg_id,))

    async def set_captcha_passed(self, tg_id: int) -> None:
        await self.db.execute("UPDATE users SET captcha_passed=1 WHERE tg_id=?", (tg_id,))
        await self.db.commit()

    async def set_role(self, tg_id: int, role: str) -> None:
        await self.db.execute("UPDATE users SET role=? WHERE tg_id=?", (role, tg_id))
        await self.db.commit()

    async def get_setting(self, key: str, default: str = "") -> str:
        val = await self.db.fetchval("SELECT value FROM settings WHERE key=?", (key,))
        if val is None or val == "":
            return default
        return str(val)

    async def set_setting(self, key: str, value: str) -> None:
        await self.db.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await self.db.commit()

    async def text(self, key: str) -> str:
        db_key = f"text_{key}"
        stored = await self.get_setting(db_key, "")
        if stored:
            return stored
        return DEFAULT_TEXTS.get(key, key)

    async def robux_rates(self) -> tuple[float, float]:
        sell = float(await self.get_setting("robux_sell_rate", "3"))
        buy = float(await self.get_setting("robux_buy_rate", "4"))
        return sell, buy

    async def list_products(
        self,
        rarity: str | None = None,
        pet_type: str | None = None,
        price_from: float | None = None,
        price_to: float | None = None,
        only_stock: bool = False,
    ) -> list:
        sql = "SELECT * FROM products WHERE 1=1"
        params: list[Any] = []
        if rarity:
            sql += " AND rarity=?"
            params.append(rarity)
        if pet_type:
            sql += " AND pet_type=?"
            params.append(pet_type)
        if price_from is not None:
            sql += " AND price_rub>=?"
            params.append(price_from)
        if price_to is not None:
            sql += " AND price_rub<=?"
            params.append(price_to)
        if only_stock:
            sql += " AND in_stock=1"
        sql += " ORDER BY price_rub ASC, id ASC"
        return await self.db.fetchall(sql, tuple(params))

    async def get_product(self, product_id: int):
        return await self.db.fetchone("SELECT * FROM products WHERE id=?", (product_id,))

    async def add_product(self, name: str, rarity: str, pet_type: str, price: float, description: str = "") -> int:
        cur = await self.db.execute(
            """
            INSERT INTO products(name, rarity, pet_type, price_rub, in_stock, description)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (name, rarity, pet_type, price, description),
        )
        await self.db.commit()
        return cur.lastrowid or 0

    async def update_product_price(self, product_id: int, price: float) -> None:
        await self.db.execute("UPDATE products SET price_rub=? WHERE id=?", (price, product_id))
        await self.db.commit()

    async def toggle_stock(self, product_id: int) -> int:
        await self.db.execute(
            "UPDATE products SET in_stock = CASE in_stock WHEN 1 THEN 0 ELSE 1 END WHERE id=?",
            (product_id,),
        )
        await self.db.commit()
        row = await self.get_product(product_id)
        return int(row["in_stock"]) if row else 0

    async def delete_product(self, product_id: int) -> None:
        await self.db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await self.db.commit()

    async def create_order(self, user_tg_id: int, kind: str, payload: dict[str, Any], amount_rub: float) -> int:
        cur = await self.db.execute(
            "INSERT INTO orders(user_tg_id, kind, status, payload, amount_rub) VALUES (?, ?, 'pending', ?, ?)",
            (user_tg_id, kind, _json(payload), amount_rub),
        )
        await self.db.commit()
        return cur.lastrowid or 0

    async def get_order(self, order_id: int):
        return await self.db.fetchone("SELECT * FROM orders WHERE id=?", (order_id,))

    async def set_order_status(self, order_id: int, status: str) -> None:
        await self.db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        await self.db.commit()

    async def add_deal_log(self, user_tg_id: int, title: str, amount_rub: float) -> None:
        await self.db.execute(
            "INSERT INTO deal_logs(user_tg_id, title, amount_rub) VALUES (?, ?, ?)",
            (user_tg_id, title, amount_rub),
        )
        await self.db.commit()

    async def deal_history(self, user_tg_id: int, limit: int = 10):
        return await self.db.fetchall(
            "SELECT * FROM deal_logs WHERE user_tg_id=? ORDER BY id DESC LIMIT ?",
            (user_tg_id, limit),
        )

    async def create_ticket(self, user_tg_id: int, kind: str, work_chat_id: int, order_id: int | None = None) -> int:
        cur = await self.db.execute(
            "INSERT INTO tickets(user_tg_id, kind, order_id, work_chat_id, status) VALUES (?, ?, ?, ?, 'open')",
            (user_tg_id, kind, order_id, work_chat_id),
        )
        await self.db.commit()
        return cur.lastrowid or 0

    async def get_ticket(self, ticket_id: int):
        return await self.db.fetchone("SELECT * FROM tickets WHERE id=?", (ticket_id,))

    async def set_ticket_status(self, ticket_id: int, status: str) -> None:
        await self.db.execute("UPDATE tickets SET status=? WHERE id=?", (status, ticket_id))
        await self.db.commit()

    async def bind_message(self, chat_id: int, message_id: int, ticket_id: int) -> None:
        await self.db.execute(
            "INSERT OR REPLACE INTO ticket_links(chat_id, message_id, ticket_id) VALUES (?, ?, ?)",
            (chat_id, message_id, ticket_id),
        )
        await self.db.commit()

    async def ticket_by_message(self, chat_id: int, message_id: int):
        row = await self.db.fetchone(
            "SELECT ticket_id FROM ticket_links WHERE chat_id=? AND message_id=?",
            (chat_id, message_id),
        )
        if not row:
            return None
        return await self.get_ticket(int(row["ticket_id"]))

    async def active_dialog(self, user_tg_id: int):
        return await self.db.fetchone(
            """
            SELECT * FROM tickets
            WHERE user_tg_id=? AND status IN ('open', 'dialog')
            ORDER BY id DESC LIMIT 1
            """,
            (user_tg_id,),
        )

    async def all_user_ids(self) -> list[int]:
        rows = await self.db.fetchall("SELECT tg_id FROM users")
        return [int(r["tg_id"]) for r in rows]

    async def stats(self) -> dict[str, Any]:
        users = int(await self.db.fetchval("SELECT COUNT(*) FROM users") or 0)
        active = int(
            await self.db.fetchval(
                "SELECT COUNT(*) FROM orders WHERE status IN ('pending','awaiting_payment','paid','dialog')"
            )
            or 0
        )
        turnover = float(
            await self.db.fetchval(
                "SELECT COALESCE(SUM(amount_rub),0) FROM orders WHERE status IN ('paid','done','accepted')"
            )
            or 0
        )
        tickets_open = int(
            await self.db.fetchval("SELECT COUNT(*) FROM tickets WHERE status IN ('open','dialog')") or 0
        )
        return {"users": users, "active": active, "turnover": turnover, "tickets_open": tickets_open}
