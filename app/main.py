from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.db import Database, Repo, init_db
from app.handlers import setup_routers
from app.middlewares import CaptchaMiddleware, DbMiddleware, ErrorMiddleware
from app.webapp import create_webapp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def run_webapp(repo: Repo) -> web.AppRunner | None:
    if not settings.webapp_url:
        return None
    app = create_webapp(repo)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webapp_host, settings.webapp_port)
    await site.start()
    logger.info("WebApp listening on %s:%s", settings.webapp_host, settings.webapp_port)
    return runner


async def main() -> None:
    db = Database(settings.database_path)
    await db.connect()
    await init_db(db)
    repo = Repo(db)

    print("\n" + "="*50)
    print(f"[DEBUG] Что видит конфиг в settings.bot_token: {repr(settings.bot_token)}")
    print("="*50 + "\n")

    bot = Bot(token="8920061174:AAH_nI354hx8BHNrtxqigYVCfYuuKGelV6A", default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(ErrorMiddleware())
    dp.update.outer_middleware(DbMiddleware(repo))
    dp.message.middleware(CaptchaMiddleware())
    dp.callback_query.middleware(CaptchaMiddleware())
    dp.include_router(setup_routers())

    runner = await run_webapp(repo)
    logger.info("Bot polling started")
    try:
        await dp.start_polling(bot)
    finally:
        if runner:
            await runner.cleanup()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
