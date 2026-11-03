import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import config
import db
from handlers import admin, commands, user


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. Uni secret / muhit o'zgaruvchisi sifatida qo'shing.")
    if not config.ADMIN_IDS:
        logging.warning("ADMIN_IDS bo'sh: admin panel hech kimga ochilmaydi.")

    db.init()
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    # Tartib muhim: avval buyruqlar, keyin admin, oxirida umumiy QR handlerlar
    dp.include_routers(commands.router, admin.router, user.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Boshlash"),
        BotCommand(command="help", description="Yordam"),
        BotCommand(command="cancel", description="Bekor qilish"),
        BotCommand(command="id", description="Mening ID raqamim"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
