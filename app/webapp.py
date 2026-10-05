from __future__ import annotations

import json
from pathlib import Path

from aiohttp import web

from app.db.repository import Repo


HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Adopt Me Market</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    body { font-family: system-ui, sans-serif; background:#12141c; color:#f4f4f8; margin:0; padding:16px; }
    h1 { font-size:20px; }
    select, button { border-radius:10px; border:0; padding:8px 10px; margin:4px 4px 12px 0; }
    .card { background:#1d2230; border-radius:14px; padding:12px; margin-bottom:10px; }
    .price { color:#7dffb3; font-weight:700; }
    .off { opacity:.45; }
    .buy { background:#6c5ce7; color:#fff; width:100%; padding:10px; }
  </style>
</head>
<body>
  <h1>🐾 Каталог Adopt Me</h1>
  <select id="rarity"><option value="">Редкость</option></select>
  <select id="type"><option value="">Тип</option></select>
  <div id="list"></div>
  <script>
    const tg = window.Telegram.WebApp;
    tg.ready(); tg.expand();
    const rarityEl = document.getElementById('rarity');
    const typeEl = document.getElementById('type');
    const listEl = document.getElementById('list');
    ['Common','Uncommon','Rare','Ultra-Rare','Legendary'].forEach(v => {
      rarityEl.insertAdjacentHTML('beforeend', `<option>${v}</option>`);
    });
    ['Normal','Neon','Mega-Neon'].forEach(v => {
      typeEl.insertAdjacentHTML('beforeend', `<option>${v}</option>`);
    });
    async function load() {
      const q = new URLSearchParams();
      if (rarityEl.value) q.set('rarity', rarityEl.value);
      if (typeEl.value) q.set('type', typeEl.value);
      const res = await fetch('/api/products?' + q.toString());
      const items = await res.json();
      listEl.innerHTML = items.map(p => `
        <div class="card ${p.in_stock ? '' : 'off'}">
          <b>${p.name}</b> · ${p.rarity} · ${p.pet_type}<br/>
          <span class="price">${p.price_rub} РБ</span>
          ${p.in_stock ? `<button class="buy" onclick="pick(${p.id})">Купить</button>` : '<div>Нет в наличии</div>'}
        </div>`).join('') || 'Нет товаров';
    }
    function pick(id) { tg.sendData(JSON.stringify({product_id: id})); }
    rarityEl.onchange = load; typeEl.onchange = load; load();
  </script>
</body>
</html>
"""


def create_webapp(repo: Repo) -> web.Application:
    async def index(_request: web.Request) -> web.Response:
        return web.Response(text=HTML, content_type="text/html")

    async def products(request: web.Request) -> web.Response:
        rarity = request.query.get("rarity") or None
        pet_type = request.query.get("type") or None
        rows = await repo.list_products(rarity=rarity, pet_type=pet_type)
        data = [
            {
                "id": int(r["id"]),
                "name": r["name"],
                "rarity": r["rarity"],
                "pet_type": r["pet_type"],
                "price_rub": float(r["price_rub"]),
                "in_stock": bool(r["in_stock"]),
            }
            for r in rows
        ]
        return web.json_response(data)

    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/api/products", products)
    Path("data").mkdir(exist_ok=True)
    return app
