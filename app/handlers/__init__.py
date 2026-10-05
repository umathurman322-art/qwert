from aiogram import Router

from app.handlers import admin, buy, menu, profile, sell, start, support, tickets


def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(menu.router)
    root.include_router(profile.router)
    root.include_router(buy.router)
    root.include_router(sell.router)
    root.include_router(support.router)
    root.include_router(admin.router)
    root.include_router(tickets.router)
    return root
